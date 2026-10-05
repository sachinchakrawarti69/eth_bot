"""
Deribit Options Data Collector - Using Public API (No keys needed)
Collects options chain, Greeks, and volatility data
"""

import requests
import pandas as pd
from datetime import datetime
from .base import BaseCollector

class DeribitCollector(BaseCollector):
    """Collect options data from Deribit public API"""
    
    def __init__(self, currency="ETH"):
        super().__init__(currency)
        self.base_url = "https://www.deribit.com/api/v2"
        self.currency = currency
    
    def fetch_options_chain(self, instrument_name=None):
        """
        Fetch options chain data
        
        Args:
            instrument_name: Specific option instrument
        
        Returns:
            dict with options data
        """
        if instrument_name is None:
            # Default to a specific option (you can modify this)
            instrument_name = f"{self.currency}-27JUN25-C-3000"
        
        endpoint = f"{self.base_url}/public/get_book_summary_by_instrument"
        params = {'instrument_name': instrument_name}
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = data.get('result', [])
            if result:
                return result[0]
            return None
            
        except Exception as e:
            print(f"❌ Error fetching options chain: {e}")
            return None
    
    def fetch_greeks(self, instrument_name="ETH-27JUN25-C-3000"):
        """
        Fetch Greeks for a specific option
        
        Args:
            instrument_name: Option instrument
        
        Returns:
            dict with Greek values
        """
        endpoint = f"{self.base_url}/public/get_greeks"
        params = {'instrument_name': instrument_name}
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = data.get('result', {})
            return {
                'delta': result.get('delta', 0),
                'gamma': result.get('gamma', 0),
                'theta': result.get('theta', 0),
                'vega': result.get('vega', 0),
                'rho': result.get('rho', 0),
                'volatility': result.get('volatility', 0),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error fetching greeks: {e}")
            return None
    
    def fetch_volatility_index(self):
        """
        Fetch volatility index data
        
        Returns:
            dict with volatility data
        """
        endpoint = f"{self.base_url}/public/get_volatility_index_data"
        params = {'currency': self.currency}
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = data.get('result', [])
            if result:
                return {
                    'volatility': result[0].get('volatility', 0),
                    'timestamp': datetime.now()
                }
            return None
            
        except Exception as e:
            print(f"❌ Error fetching volatility: {e}")
            return None
    
    def fetch_instruments(self):
        """
        Fetch all available instruments
        
        Returns:
            list of instrument names
        """
        endpoint = f"{self.base_url}/public/get_instruments"
        params = {
            'currency': self.currency,
            'kind': 'option'
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            instruments = data.get('result', [])
            return [inst['instrument_name'] for inst in instruments]
            
        except Exception as e:
            print(f"❌ Error fetching instruments: {e}")
            return []
    
    def fetch_option_summary(self):
        """
        Fetch option market summary
        
        Returns:
            dict with option summary data
        """
        endpoint = f"{self.base_url}/public/get_option_markets"
        params = {'currency': self.currency}
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('result', {})
            
        except Exception as e:
            print(f"❌ Error fetching option summary: {e}")
            return None

# Test the collector
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Deribit Collector...")
    print("=" * 60)
    
    collector = DeribitCollector()
    
    # Test instruments
    print("\n📋 Fetching instruments...")
    instruments = collector.fetch_instruments()
    print(f"   Found {len(instruments)} instruments")
    if instruments:
        print(f"   Example: {instruments[0]}")
    
    # Test options chain
    print("\n📊 Fetching options chain...")
    option = collector.fetch_options_chain()
    if option:
        print(f"   Instrument: {option.get('instrument_name', 'N/A')}")
        print(f"   Bid: ${option.get('bid_price', 0):,.2f}")
        print(f"   Ask: ${option.get('ask_price', 0):,.2f}")
        print(f"   IV: {option.get('iv', 0):.2f}%")
    
    # Test Greeks
    print("\n📈 Fetching Greeks...")
    greeks = collector.fetch_greeks()
    if greeks:
        print(f"   Delta: {greeks['delta']:.4f}")
        print(f"   Gamma: {greeks['gamma']:.4f}")
        print(f"   Theta: {greeks['theta']:.4f}")
        print(f"   Vega: {greeks['vega']:.4f}")
        print(f"   Volatility: {greeks['volatility']:.2f}%")
    
    # Test volatility
    print("\n📉 Fetching volatility index...")
    vol = collector.fetch_volatility_index()
    if vol:
        print(f"   Volatility: {vol['volatility']:.2f}%")
    
    print("\n" + "=" * 60)
    print("✅ Deribit collector test complete!")
    print("=" * 60)