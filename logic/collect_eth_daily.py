#!/usr/bin/env python3
"""
Daily ETH OHLCV Data Collector
Stores Open, High, Low, Close, Volume data in CSV, SQLite, and JSON
"""

import requests
import pandas as pd
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import time

# ==================== CONFIGURATION ====================
DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "Eth_OHLCV.csv"
DB_PATH = DATA_DIR / "ETH.db"
JSON_PATH = DATA_DIR / "Eth_OHLCV.json"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# ==================== FETCH OHLCV DATA ====================
def fetch_eth_ohlcv(days=365):
    """
    Fetch daily OHLCV data for Ethereum
    Using Binance API (more reliable for OHLCV data)
    """
    print(f"📊 Fetching {days} days of ETH OHLCV data...")
    
    # Binance API for OHLCV data
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': 'ETHUSDT',
        'interval': '1d',  # Daily candles
        'limit': days
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Parse OHLCV data
        ohlcv_data = []
        for candle in data:
            ohlcv_data.append({
                'date': datetime.fromtimestamp(candle[0] / 1000),  # Open time
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5]),
                'close_time': datetime.fromtimestamp(candle[6] / 1000),
                'quote_volume': float(candle[7]),
                'trades': int(candle[8]),
                'taker_buy_base': float(candle[9]),
                'taker_buy_quote': float(candle[10])
            })
        
        df = pd.DataFrame(ohlcv_data)
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"✅ Fetched {len(df)} days of OHLCV data")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        raise
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        raise

# ==================== ALTERNATIVE: CoinGecko OHLCV ====================
def fetch_eth_ohlcv_coingecko(days=365):
    """
    Alternative: Fetch OHLCV from CoinGecko
    Note: CoinGecko provides OHLC but volume needs to be fetched separately
    """
    print(f"📊 Fetching {days} days of ETH OHLCV from CoinGecko...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Fetch OHLC data
    ohlc_url = "https://api.coingecko.com/api/v3/coins/ethereum/ohlc"
    ohlc_params = {
        'vs_currency': 'usd',
        'days': days
    }
    
    # Fetch volume data
    volume_url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart/range"
    volume_params = {
        'vs_currency': 'usd',
        'from': int(start_date.timestamp()),
        'to': int(end_date.timestamp())
    }
    
    try:
        # Get OHLC data
        ohlc_response = requests.get(ohlc_url, params=ohlc_params, timeout=30)
        ohlc_response.raise_for_status()
        ohlc_data = ohlc_response.json()
        
        # Get volume data
        volume_response = requests.get(volume_url, params=volume_params, timeout=30)
        volume_response.raise_for_status()
        volume_data = volume_response.json()
        
        # Create DataFrames
        ohlc_df = pd.DataFrame(ohlc_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        ohlc_df['date'] = pd.to_datetime(ohlc_df['timestamp'], unit='ms')
        
        volume_df = pd.DataFrame(volume_data['total_volumes'], columns=['timestamp', 'volume'])
        volume_df['date'] = pd.to_datetime(volume_df['timestamp'], unit='ms')
        
        # Merge OHLC with volume
        df = pd.merge(ohlc_df, volume_df[['date', 'volume']], on='date', how='left')
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"✅ Fetched {len(df)} days of OHLCV data from CoinGecko")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching from CoinGecko: {e}")
        raise

# ==================== STORE IN CSV ====================
def save_to_csv(df):
    """Save OHLCV data to CSV file"""
    try:
        if df is None or len(df) == 0:
            print("⚠️ No data to save to CSV")
            return
            
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # If CSV exists, merge with new data
        if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
            try:
                existing_df = pd.read_csv(CSV_PATH, parse_dates=['date'])
                if not existing_df.empty:
                    combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['date'], keep='last')
                    combined_df = combined_df.sort_values('date').reset_index(drop=True)
                    combined_df.to_csv(CSV_PATH, index=False)
                    print(f"📁 CSV updated: {CSV_PATH} ({len(combined_df)} records)")
                    return
            except Exception as e:
                print(f"⚠️ Could not read existing CSV: {e}")
                df.to_csv(CSV_PATH, index=False)
                print(f"📁 CSV overwritten: {CSV_PATH} ({len(df)} records)")
                return
        
        df.to_csv(CSV_PATH, index=False)
        print(f"📁 CSV created: {CSV_PATH} ({len(df)} records)")
        
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")

# ==================== STORE IN SQLITE ====================
def save_to_sqlite(df):
    """Save OHLCV data to SQLite database"""
    try:
        if df is None or len(df) == 0:
            print("⚠️ No data to save to SQLite")
            return
            
        conn = sqlite3.connect(DB_PATH)
        
        # Create table with OHLCV schema
        conn.execute('''
            CREATE TABLE IF NOT EXISTS eth_ohlcv (
                date TEXT PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL
            )
        ''')
        
        # Convert date to string for SQLite
        df_sqlite = df.copy()
        df_sqlite['date'] = df_sqlite['date'].dt.strftime('%Y-%m-%d')
        
        # Insert or replace data
        df_sqlite.to_sql('eth_ohlcv', conn, if_exists='replace', index=False)
        
        # Verify
        count = conn.execute("SELECT COUNT(*) FROM eth_ohlcv").fetchone()[0]
        conn.close()
        
        print(f"🗄️ SQLite updated: {DB_PATH} ({count} records)")
        
    except Exception as e:
        print(f"❌ Error saving SQLite: {e}")

# ==================== STORE IN JSON ====================
def save_to_json(df):
    """Save OHLCV data to JSON file"""
    try:
        if df is None or len(df) == 0:
            print("⚠️ No data to save to JSON")
            return
            
        # Convert DataFrame to JSON with proper date formatting
        df_json = df.copy()
        df_json['date'] = df_json['date'].dt.strftime('%Y-%m-%d')
        
        # Create JSON with metadata
        json_data = {
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'total_records': len(df_json),
                'source': 'Binance API',
                'currency': 'USDT',
                'interval': '1d',
                'fields': ['date', 'open', 'high', 'low', 'close', 'volume']
            },
            'data': df_json.to_dict(orient='records')
        }
        
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 JSON updated: {JSON_PATH} ({len(df_json)} records)")
        
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")

# ==================== VERIFY DATA ====================
def verify_data():
    """Verify all data stores"""
    print("\n🔍 Verifying data integrity...")
    
    try:
        # Check CSV
        if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
            csv_df = pd.read_csv(CSV_PATH, parse_dates=['date'])
            latest = csv_df.iloc[-1]
            print(f"  ✅ CSV: {len(csv_df)} records")
            print(f"     Latest: {latest['date']} | O:{latest['open']:.2f} H:{latest['high']:.2f} L:{latest['low']:.2f} C:{latest['close']:.2f} V:{latest['volume']:,.0f}")
        else:
            print("  ⚠️ CSV: File is empty or doesn't exist")
        
        # Check SQLite
        if DB_PATH.exists() and DB_PATH.stat().st_size > 0:
            conn = sqlite3.connect(DB_PATH)
            try:
                sqlite_count = conn.execute("SELECT COUNT(*) FROM eth_ohlcv").fetchone()[0]
                latest = conn.execute("SELECT * FROM eth_ohlcv ORDER BY date DESC LIMIT 1").fetchone()
                if latest:
                    print(f"  ✅ SQLite: {sqlite_count} records")
                    print(f"     Latest: {latest[0]} | O:{latest[1]:.2f} H:{latest[2]:.2f} L:{latest[3]:.2f} C:{latest[4]:.2f} V:{latest[5]:,.0f}")
            except:
                print("  ⚠️ SQLite: Table exists but might be empty")
            finally:
                conn.close()
        else:
            print("  ⚠️ SQLite: Database file doesn't exist or is empty")
        
        # Check JSON
        if JSON_PATH.exists() and JSON_PATH.stat().st_size > 0:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            latest = json_data['data'][-1] if json_data['data'] else None
            print(f"  ✅ JSON: {json_data['metadata']['total_records']} records")
            if latest:
                print(f"     Latest: {latest['date']} | O:{latest['open']:.2f} H:{latest['high']:.2f} L:{latest['low']:.2f} C:{latest['close']:.2f}")
        else:
            print("  ⚠️ JSON: File is empty or doesn't exist")
            
    except Exception as e:
        print(f"  ❌ Verification error: {e}")

# ==================== CALCULATE TECHNICAL INDICATORS ====================
def add_technical_indicators(df):
    """Add useful technical indicators to the data"""
    if df is None or len(df) < 20:
        return df
    
    df = df.copy()
    
    # Simple Moving Averages
    df['SMA_7'] = df['close'].rolling(window=7).mean()
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    
    # Exponential Moving Average
    df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
    
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    
    # Average True Range (ATR)
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR_14'] = true_range.rolling(window=14).mean()
    
    return df

# ==================== MAIN EXECUTION ====================
def main():
    print("=" * 60)
    print("🚀 ETH Daily OHLCV Data Collector")
    print("=" * 60)
    
    try:
        # Fetch OHLCV data (using Binance)
        df = fetch_eth_ohlcv(days=365)
        
        # Alternative: Use CoinGecko (uncomment if Binance doesn't work)
        # df = fetch_eth_ohlcv_coingecko(days=365)
        
        if df is None or len(df) == 0:
            print("❌ No data fetched. Please check your internet connection.")
            return
        
        # Add technical indicators
        print("\n📊 Calculating technical indicators...")
        df = add_technical_indicators(df)
        
        # Show data summary
        print(f"\n📊 Data Summary:")
        print(f"   Period: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        print(f"   Latest Close: ${df['close'].iloc[-1]:.2f}")
        print(f"   High: ${df['high'].max():.2f}")
        print(f"   Low: ${df['low'].min():.2f}")
        print(f"   Average Volume: {df['volume'].mean():,.0f}")
        
        # Save to all formats
        print("\n💾 Saving OHLCV data...")
        save_to_csv(df)
        save_to_sqlite(df)
        save_to_json(df)
        
        # Verify
        verify_data()
        
        print("\n" + "=" * 60)
        print("✅ All done! OHLCV data collected and stored in 3 formats.")
        print(f"📂 Data directory: {DATA_DIR.absolute()}")
        
        # Show sample of latest data
        print("\n📋 Latest 5 days of OHLCV data:")
        display_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        print(df[display_cols].tail(5).to_string(index=False))
        
        # Show technical indicators sample
        print("\n📊 Technical Indicators (last 5 days):")
        tech_cols = ['date', 'SMA_20', 'RSI_14', 'MACD', 'BB_upper', 'BB_lower']
        print(df[tech_cols].tail(5).to_string(index=False))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Troubleshooting tips:")
        print("  1. Check your internet connection")
        print("  2. Try using CoinGecko alternative (uncomment in code)")
        print("  3. Make sure you have all required libraries: pip install pandas requests")

if __name__ == "__main__":
    main()