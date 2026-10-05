"""
Binance Data Collector - Using Public API (No keys needed)
Collects OHLCV, ticker, and orderbook data
"""

import sys
from pathlib import Path

# Handle both standalone and module imports
try:
    from .base import BaseCollector
except ImportError:
    # Add project root to path for standalone execution
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from collectors.base import BaseCollector

import requests
import pandas as pd
from datetime import datetime

class BinanceCollector(BaseCollector):
    """Collect data from Binance public API"""
    
    def __init__(self, symbol="ETH/USDT", timeframe="1h"):
        super().__init__(symbol)
        self.timeframe = timeframe
        self.base_url = "https://api.binance.com"
        self.symbol_clean = symbol.replace("/", "")
    
    def fetch(self, limit=100, data_type="ohlcv"):
        """
        Main fetch method - implements abstract method
        
        Args:
            limit: Number of records to fetch
            data_type: Type of data ('ohlcv', 'ticker', 'orderbook')
        
        Returns:
            Fetched data
        """
        if data_type == "ohlcv":
            return self.fetch_ohlcv(limit)
        elif data_type == "ticker":
            return self.fetch_ticker()
        elif data_type == "orderbook":
            return self.fetch_orderbook(limit)
        else:
            print(f"❌ Unknown data_type: {data_type}")
            return None
    
    def fetch_ohlcv(self, limit=100):
        """
        Fetch OHLCV (candlestick) data
        
        Args:
            limit: Number of candles to fetch (max 1000)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        endpoint = f"{self.base_url}/api/v3/klines"
        params = {
            'symbol': self.symbol_clean,
            'interval': self.timeframe,
            'limit': limit
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # Convert to numeric
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col])
            
            # Select only needed columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            print(f"✅ Fetched {len(df)} candles for {self.symbol}")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error fetching OHLCV: {e}")
            return None
        except Exception as e:
            print(f"❌ Error fetching OHLCV: {e}")
            return None
    
    def fetch_ticker(self):
        """
        Fetch current 24hr ticker data
        
        Returns:
            dict with price, volume, high, low, change
        """
        endpoint = f"{self.base_url}/api/v3/ticker/24hr"
        params = {'symbol': self.symbol_clean}
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'symbol': data['symbol'],
                'price': float(data['lastPrice']),
                'volume': float(data['volume']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'change': float(data['priceChangePercent']),
                'change_abs': float(data['priceChange']),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error fetching ticker: {e}")
            return None
    
    def fetch_orderbook(self, limit=10):
        """
        Fetch current order book
        
        Args:
            limit: Number of bids/asks to fetch (max 100)
        
        Returns:
            dict with bids, asks, timestamp
        """
        endpoint = f"{self.base_url}/api/v3/depth"
        params = {
            'symbol': self.symbol_clean,
            'limit': limit
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'bids': [[float(x[0]), float(x[1])] for x in data['bids'][:5]],
                'asks': [[float(x[0]), float(x[1])] for x in data['asks'][:5]],
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error fetching orderbook: {e}")
            return None
    
    def fetch_agg_trades(self, limit=100):
        """
        Fetch aggregate trades
        
        Args:
            limit: Number of trades to fetch
        
        Returns:
            DataFrame with trade data
        """
        endpoint = f"{self.base_url}/api/v3/aggTrades"
        params = {
            'symbol': self.symbol_clean,
            'limit': limit
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data)
            df['time'] = pd.to_datetime(df['T'], unit='ms')
            
            return df[['a', 'p', 'q', 'T', 'm', 'time']]
            
        except Exception as e:
            print(f"❌ Error fetching trades: {e}")
            return None
    
    def fetch_historical(self, days=30):
        """
        Fetch historical OHLCV data for multiple days
        
        Args:
            days: Number of days to fetch
        
        Returns:
            DataFrame with OHLCV data
        """
        limit = min(days * 24, 1000)  # Approximate candles
        return self.fetch_ohlcv(limit=limit)

# Test the collector (only runs when file is executed directly)
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Binance Collector...")
    print("=" * 60)
    
    collector = BinanceCollector()
    
    # Test fetch method
    print("\n📊 Testing fetch() method...")
    df = collector.fetch(limit=5, data_type="ohlcv")
    if df is not None:
        print(df[['timestamp', 'close', 'volume']].to_string(index=False))
    
    # Test OHLCV
    print("\n📊 Fetching OHLCV...")
    df = collector.fetch_ohlcv(10)
    if df is not None:
        print(df[['timestamp', 'close', 'volume']].to_string(index=False))
    
    # Test Ticker
    print("\n📈 Fetching Ticker...")
    ticker = collector.fetch_ticker()
    if ticker:
        print(f"   Symbol: {ticker['symbol']}")
        print(f"   Price: ${ticker['price']:,.2f}")
        print(f"   24h Change: {ticker['change']:.2f}%")
        print(f"   24h Volume: ${ticker['volume']:,.2f}")
    
    # Test Orderbook
    print("\n📚 Fetching Orderbook...")
    book = collector.fetch_orderbook()
    if book:
        print(f"   Best Bid: ${book['bids'][0][0]:,.2f} (size: {book['bids'][0][1]})")
        print(f"   Best Ask: ${book['asks'][0][0]:,.2f} (size: {book['asks'][0][1]})")
        print(f"   Spread: ${book['asks'][0][0] - book['bids'][0][0]:,.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Binance collector test complete!")
    print("=" * 60)