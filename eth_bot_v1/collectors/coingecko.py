"""
CoinGecko Data Collector - Using Public API (No keys needed)
Collects price, market data, and historical data
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

class CoinGeckoCollector(BaseCollector):
    """Collect data from CoinGecko public API"""
    
    def __init__(self):
        super().__init__("ethereum")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.coin_id = "ethereum"
    
    def fetch(self, data_type="price", **kwargs):
        """
        Main fetch method - implements abstract method
        
        Args:
            data_type: Type of data ('price', 'market', 'historical', 'fear_greed')
            **kwargs: Additional arguments
        
        Returns:
            Fetched data
        """
        if data_type == "price":
            return self.fetch_price()
        elif data_type == "market":
            return self.fetch_market_data()
        elif data_type == "historical":
            days = kwargs.get('days', 30)
            return self.fetch_historical(days)
        elif data_type == "fear_greed":
            return self.fetch_fear_greed()
        else:
            print(f"❌ Unknown data_type: {data_type}")
            return None
    
    def fetch_price(self):
        """
        Fetch current ETH price in USD
        
        Returns:
            float: Current price in USD
        """
        endpoint = f"{self.base_url}/simple/price"
        params = {
            'ids': self.coin_id,
            'vs_currencies': 'usd'
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            price = data[self.coin_id]['usd']
            print(f"💰 ETH Price: ${price:,.2f}")
            return price
        except Exception as e:
            print(f"❌ Error fetching price: {e}")
            return None
    
    def fetch_market_data(self):
        """
        Fetch comprehensive market data
        
        Returns:
            dict with market data
        """
        endpoint = f"{self.base_url}/coins/{self.coin_id}"
        
        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            market = data['market_data']
            
            return {
                'price': market['current_price']['usd'],
                'market_cap': market['market_cap']['usd'],
                'volume_24h': market['total_volume']['usd'],
                'price_change_24h': market['price_change_percentage_24h'],
                'price_change_7d': market['price_change_percentage_7d'],
                'high_24h': market['high_24h']['usd'],
                'low_24h': market['low_24h']['usd'],
                'circulating_supply': market['circulating_supply'],
                'total_supply': market['total_supply'],
                'ath': market['ath']['usd'],
                'atl': market['atl']['usd'],
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error fetching market data: {e}")
            return None
    
    def fetch_historical(self, days=30):
        """
        Fetch historical price data
        
        Args:
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
        
        Returns:
            dict with price, market cap, and volume data
        """
        endpoint = f"{self.base_url}/coins/{self.coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Prices
            prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            prices['timestamp'] = pd.to_datetime(prices['timestamp'], unit='ms')
            
            # Market caps
            market_caps = pd.DataFrame(data['market_caps'], columns=['timestamp', 'market_cap'])
            market_caps['timestamp'] = pd.to_datetime(market_caps['timestamp'], unit='ms')
            
            # Volumes
            volumes = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
            volumes['timestamp'] = pd.to_datetime(volumes['timestamp'], unit='ms')
            
            return {
                'prices': prices,
                'market_caps': market_caps,
                'volumes': volumes
            }
            
        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return None
    
    def fetch_fear_greed(self):
        """
        Fetch Fear and Greed Index
        
        Returns:
            dict with value and classification
        """
        url = "https://api.alternative.me/fng/"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'value': int(data['data'][0]['value']),
                'classification': data['data'][0]['value_classification'],
                'timestamp': datetime.fromtimestamp(int(data['data'][0]['timestamp']))
            }
            
        except Exception as e:
            print(f"❌ Error fetching fear/greed: {e}")
            return None

# Test the collector (only runs when file is executed directly)
if __name__ == "__main__":
    print("=" * 60)
    print("Testing CoinGecko Collector...")
    print("=" * 60)
    
    collector = CoinGeckoCollector()
    
    # Test fetch method
    print("\n📊 Testing fetch() method...")
    price = collector.fetch(data_type="price")
    if price:
        print(f"   Price: ${price:,.2f}")
    
    # Test price
    print("\n💰 Fetching price...")
    price = collector.fetch_price()
    
    # Test market data
    print("\n📊 Fetching market data...")
    market = collector.fetch_market_data()
    if market:
        print(f"   Price: ${market['price']:,.2f}")
        print(f"   Market Cap: ${market['market_cap']:,.0f}")
        print(f"   24h Volume: ${market['volume_24h']:,.0f}")
        print(f"   24h Change: {market['price_change_24h']:.2f}%")
        print(f"   7d Change: {market['price_change_7d']:.2f}%")
        print(f"   24h High: ${market['high_24h']:,.2f}")
        print(f"   24h Low: ${market['low_24h']:,.2f}")
    
    # Test Fear/Greed
    print("\n😱 Fetching Fear/Greed Index...")
    fg = collector.fetch_fear_greed()
    if fg:
        print(f"   Value: {fg['value']}")
        print(f"   Classification: {fg['classification']}")
    
    # Test historical data
    print("\n📈 Fetching historical data (7 days)...")
    historical = collector.fetch_historical(7)
    if historical:
        print(f"   Price points: {len(historical['prices'])}")
        print(f"   Latest price: ${historical['prices']['price'].iloc[-1]:,.2f}")
    
    print("\n" + "=" * 60)
    print("✅ CoinGecko collector test complete!")
    print("=" * 60)