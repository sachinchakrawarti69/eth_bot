# Trading helper functions 
import pandas as pd
import numpy as np

class TradingHelpers:
    """Trading helper functions"""
    
    @staticmethod
    def calculate_returns(df, price_col='close'):
        """Calculate percentage returns"""
        df['returns'] = df[price_col].pct_change() * 100
        return df
    
    @staticmethod
    def calculate_volatility(df, period=20, price_col='close'):
        """Calculate rolling volatility"""
        df['volatility'] = df[price_col].pct_change().rolling(period).std() * 100
        return df
    
    @staticmethod
    def calculate_drawdown(df, price_col='close'):
        """Calculate drawdown"""
        rolling_max = df[price_col].expanding().max()
        df['drawdown'] = (df[price_col] / rolling_max - 1) * 100
        return df