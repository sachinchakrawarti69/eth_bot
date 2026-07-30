# Visualization functions for OHLCV 
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class TradingVisualizer:
    """Visualization utilities for trading data"""
    
    @staticmethod
    def plot_candlestick(df, title="Candlestick Chart", figsize=(15, 6)):
        """Plot a candlestick chart (simplified)"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot price line
        ax.plot(df.index, df['close'], label='Close', linewidth=2)
        ax.fill_between(df.index, df['low'], df['high'], alpha=0.2)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price ($)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_price_volume(df, figsize=(15, 8)):
        """Plot price and volume in subplots"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
        
        # Price
        ax1.plot(df.index, df['close'], label='Close', linewidth=2)
        ax1.fill_between(df.index, df['low'], df['high'], alpha=0.2)
        ax1.set_title('ETH Price', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price ($)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Volume
        ax2.bar(df.index, df['volume'], color='orange', alpha=0.7)
        ax2.set_title('Volume', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Volume')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()