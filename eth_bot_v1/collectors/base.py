"""
Base Collector Class
Abstract base class for all data collectors
"""

import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

class BaseCollector(ABC):
    """Abstract base class for all collectors"""
    
    def __init__(self, symbol="ETH/USDT"):
        self.symbol = symbol
        self.timestamp = datetime.now()
    
    @abstractmethod
    def fetch(self, **kwargs):
        """Fetch data from source - to be implemented by child classes"""
        pass
    
    def to_dataframe(self, data):
        """Convert data to pandas DataFrame"""
        if isinstance(data, pd.DataFrame):
            return data
        return pd.DataFrame(data)
    
    def save_to_csv(self, df, filename):
        """Save DataFrame to CSV file"""
        if df is None or df.empty:
            print("⚠️ No data to save")
            return None
            
        try:
            # Ensure raw directory exists
            raw_dir = Path("data/raw")
            raw_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = raw_dir / filename
            df.to_csv(filepath, index=False)
            print(f"✅ Saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
            return None
    
    def get_current_time(self):
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(symbol={self.symbol})"