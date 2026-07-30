"""
Market Depth Analysis from Binance
"""
import requests
import pandas as pd
import numpy as np

class MarketDepthAnalyzer:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
    
    def get_order_book(self, symbol="ETHUSDT", limit=100):
        """Get order book depth"""
        params = {'symbol': symbol, 'limit': limit}
        response = requests.get(f"{self.base_url}/depth", params=params)
        data = response.json()
        
        bids = pd.DataFrame(data['bids'], columns=['price', 'quantity']).astype(float)
        asks = pd.DataFrame(data['asks'], columns=['price', 'quantity']).astype(float)
        
        return bids, asks
    
    def calculate_imbalance(self, symbol="ETHUSDT"):
        """Calculate buy/sell imbalance"""
        bids, asks = self.get_order_book(symbol)
        
        # Calculate cumulative volume
        bid_volume = bids['quantity'].sum()
        ask_volume = asks['quantity'].sum()
        
        # Calculate weighted average prices
        bid_wap = (bids['price'] * bids['quantity']).sum() / bid_volume if bid_volume > 0 else 0
        ask_wap = (asks['price'] * asks['quantity']).sum() / ask_volume if ask_volume > 0 else 0
        
        # Imbalance ratio
        imbalance_ratio = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
        
        return {
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'bid_wap': bid_wap,
            'ask_wap': ask_wap,
            'spread': ask_wap - bid_wap,
            'imbalance_ratio': imbalance_ratio,
            'signal': 'BUY' if imbalance_ratio > 0.3 else ('SELL' if imbalance_ratio < -0.3 else 'NEUTRAL')
        }

# Add to config.py
# MARKET_DEPTH_ENABLED = True