"""
Free On-Chain Data from Etherscan
"""
import requests
import pandas as pd
from datetime import datetime

class OnChainAnalyzer:
    def __init__(self):
        # Free Etherscan API (get key from etherscan.io)
        self.api_key = "YOUR_ETHERSCAN_API_KEY"  # Free signup
        self.base_url = "https://api.etherscan.io/api"
    
    def get_total_supply(self):
        """Get total ETH supply"""
        params = {
            'module': 'stats',
            'action': 'ethsupply',
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        return response.json().get('result', 0)
    
    def get_gas_price(self):
        """Get current gas price"""
        params = {
            'module': 'gastracker',
            'action': 'gasoracle',
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        data = response.json().get('result', {})
        return {
            'slow': float(data.get('SafeGasPrice', 0)),
            'average': float(data.get('ProposeGasPrice', 0)),
            'fast': float(data.get('FastGasPrice', 0))
        }
    
    def get_daily_transactions(self):
        """Get daily transaction count"""
        params = {
            'module': 'stats',
            'action': 'dailytx',
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        return response.json().get('result', [])
    
    def get_eth_price(self):
        """Get ETH price from Etherscan"""
        params = {
            'module': 'stats',
            'action': 'ethprice',
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        data = response.json().get('result', {})
        return {
            'usd': float(data.get('ethusd', 0)),
            'btc': float(data.get('ethbtc', 0))
        }

# Add to config.py
# ONCHAIN_ENABLED = True