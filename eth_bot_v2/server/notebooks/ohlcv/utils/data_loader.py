# Data loading utilities for OHLCV 
import pandas as pd
import numpy as np
from pathlib import Path
import sqlite3
import json
from typing import Optional, Dict, List

class DataLoader:
    """Load and prepare OHLCV data from various sources"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / 'data'
        self.db_path = self.data_dir / 'ETH.db'
        self.csv_path = self.data_dir / 'Eth_OHLCV.csv'
        self.json_path = self.data_dir / 'Eth_OHLCV.json'
    
    def load_from_csv(self) -> pd.DataFrame:
        """Load data from CSV file"""
        try:
            if self.csv_path.exists():
                df = pd.read_csv(self.csv_path)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                print(f"✅ Loaded {len(df)} rows from CSV")
                return df
            else:
                print(f"⚠️  CSV file not found: {self.csv_path}")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return pd.DataFrame()
    
    def load_from_json(self) -> pd.DataFrame:
        """Load data from JSON file"""
        try:
            if self.json_path.exists():
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                print(f"✅ Loaded {len(df)} rows from JSON")
                return df
            else:
                print(f"⚠️  JSON file not found: {self.json_path}")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            return pd.DataFrame()
    
    def load_from_db(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Load data from SQLite database"""
        try:
            if not self.db_path.exists():
                print(f"⚠️  Database not found: {self.db_path}")
                return pd.DataFrame()
            
            conn = sqlite3.connect(str(self.db_path))
            query = "SELECT * FROM price_data ORDER BY timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            print(f"✅ Loaded {len(df)} rows from database")
            return df
        except Exception as e:
            print(f"❌ Error loading from database: {e}")
            return pd.DataFrame()