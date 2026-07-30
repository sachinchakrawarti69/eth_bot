"""
Interactive Trading Dashboard
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

db_path = Path('..') / 'data' / 'ETH.db'

def load_data():
    conn = sqlite3.connect(db_path)
    
    # Load OHLCV
    ohlcv = pd.read_sql("SELECT * FROM eth_ohlcv ORDER BY date", conn, parse_dates=['date'])
    
    # Load signals
    signals = pd.read_sql("SELECT * FROM signals ORDER BY id", conn)
    
    # Load trades
    trades = pd.read_sql("SELECT * FROM trades ORDER BY id", conn)
    
    conn.close()
    return ohlcv, signals, trades

def plot_price_with_signals(ohlcv, signals):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Price chart
    ax1.plot(ohlcv['date'], ohlcv['close'], label='Close Price', color='black')
    ax1.set_title('ETH Price with Trading Signals')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price (USD)')
    ax1.grid(True, alpha=0.3)
    
    # Add signals
    buy_signals = signals[signals['signal_type'] == 'BUY']
    sell_signals = signals[signals['signal_type'] == 'SELL']
    
    if len(buy_signals) > 0:
        ax1.scatter(buy_signals['timestamp'], buy_signals['current_price'], 
                   color='green', s=100, marker='^', label='BUY')
    if len(sell_signals) > 0:
        ax1.scatter(sell_signals['timestamp'], sell_signals['current_price'], 
                   color='red', s=100, marker='v', label='SELL')
    
    ax1.legend()
    
    # Confidence chart
    if len(signals) > 0:
        ax2.plot(signals['timestamp'], signals['confidence'], color='blue')
        ax2.axhline(y=0.60, color='red', linestyle='--', label='Threshold (60%)')
        ax2.set_title('Signal Confidence Over Time')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Confidence')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
    
    plt.tight_layout()
    plt.show()

def dashboard():
    print("=" * 60)
    print("📊 ETH TRADING DASHBOARD")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    ohlcv, signals, trades = load_data()
    
    # Price
    if len(ohlcv) > 0:
        current_price = ohlcv['close'].iloc[-1]
        print(f"💰 Current Price: ${current_price:.2f}")
        
        # Daily change
        if len(ohlcv) > 1:
            daily_change = (current_price - ohlcv['close'].iloc[-2]) / ohlcv['close'].iloc[-2] * 100
            print(f"📈 Daily Change: {daily_change:+.2f}%")
    
    # Signals
    print(f"\n📊 Total Signals: {len(signals)}")
    if len(signals) > 0:
        latest = signals.iloc[-1]
        print(f"   Latest: {latest['signal_type']} (Conf: {latest['confidence']*100:.1f}%)")
    
    # Trades
    print(f"\n💼 Total Trades: {len(trades)}")
    if len(trades) > 0:
        total_pnl = trades['pnl'].sum() if 'pnl' in trades else 0
        win_rate = len(trades[trades['pnl'] > 0]) / len(trades) * 100
        print(f"💰 Total P&L: ${total_pnl:.2f}")
        print(f"📈 Win Rate: {win_rate:.1f}%")
    
    # Plot
    plot = input("\n📊 Show price chart? (y/n): ")
    if plot.lower() == 'y':
        plot_price_with_signals(ohlcv, signals)
    
    print("=" * 60)

if __name__ == "__main__":
    dashboard()