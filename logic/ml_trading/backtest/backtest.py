"""
Backtest trading strategy
"""
import pandas as pd
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt

db_path = Path('..') / 'data' / 'ETH.db'

class Backtester:
    def __init__(self, initial_balance=1000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0
        self.trades = []
    
    def backtest(self, df, signal_column='signal'):
        """Backtest strategy"""
        balance = self.initial_balance
        position = 0
        entry_price = 0
        
        for idx, row in df.iterrows():
            if row[signal_column] == 'BUY' and position == 0:
                # Buy
                position = balance / row['close']
                balance = 0
                entry_price = row['close']
                self.trades.append({
                    'date': row['date'],
                    'type': 'BUY',
                    'price': row['close'],
                    'quantity': position
                })
            
            elif row[signal_column] == 'SELL' and position > 0:
                # Sell
                balance = position * row['close']
                pnl = balance - self.initial_balance
                position = 0
                self.trades.append({
                    'date': row['date'],
                    'type': 'SELL',
                    'price': row['close'],
                    'quantity': position,
                    'pnl': pnl
                })
        
        # Close position at end
        if position > 0:
            balance = position * df.iloc[-1]['close']
            self.trades.append({
                'date': df.iloc[-1]['date'],
                'type': 'CLOSE',
                'price': df.iloc[-1]['close'],
                'pnl': balance - self.initial_balance
            })
        
        return {
            'final_balance': balance,
            'total_return': (balance - self.initial_balance) / self.initial_balance * 100,
            'total_trades': len([t for t in self.trades if t['type'] == 'SELL']),
            'final_price': df.iloc[-1]['close']
        }

if __name__ == "__main__":
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM eth_ohlcv ORDER BY date", conn, parse_dates=['date'])
    conn.close()
    
    # Add mock signals (for testing)
    df['signal'] = 'HOLD'
    df.loc[df['close'] > df['close'].rolling(20).mean(), 'signal'] = 'BUY'
    df.loc[df['close'] < df['close'].rolling(20).mean(), 'signal'] = 'SELL'
    
    backtester = Backtester()
    result = backtester.backtest(df)
    
    print("📊 Backtest Results")
    print("=" * 40)
    print(f"Initial Balance: $1000")
    print(f"Final Balance: ${result['final_balance']:.2f}")
    print(f"Total Return: {result['total_return']:.2f}%")
    print(f"Total Trades: {result['total_trades']}")