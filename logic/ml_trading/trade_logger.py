"""
Log trades to SQLite database
"""
import sqlite3
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from server.ml_trading.config import DB_PATH

class TradeLogger:
    def __init__(self):
        self.db_path = DB_PATH
        self.create_tables()
    
    def create_tables(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, type TEXT, price REAL, quantity REAL, order_id TEXT, pnl REAL, pnl_percent REAL, signal_confidence REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS performance (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, total_trades INTEGER, winning_trades INTEGER, losing_trades INTEGER, total_pnl REAL, win_rate REAL, balance REAL)")
            conn.commit()
            conn.close()
            print("Trade tables created")
        except Exception as e:
            print(f"Error: {e}")
    
    def log_trade(self, trade_data):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO trades (timestamp, type, price, quantity, order_id, pnl, pnl_percent, signal_confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                trade_data.get('timestamp', datetime.now().isoformat()),
                trade_data.get('type'), trade_data.get('price', 0),
                trade_data.get('quantity', 0), trade_data.get('order_id', ''),
                trade_data.get('pnl', 0), trade_data.get('pnl_percent', 0),
                trade_data.get('signal_confidence', 0)
            ))
            conn.commit()
            conn.close()
            print("Trade logged")
        except Exception as e:
            print(f"Error: {e}")
    
    def get_trade_history(self, limit=100):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql(f"SELECT * FROM trades ORDER BY id DESC LIMIT {limit}", conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()
    
    def get_performance_summary(self):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql("SELECT * FROM trades", conn)
            conn.close()
            if len(df) == 0:
                return {'total_trades': 0}
            return {
                'total_trades': len(df),
                'winning_trades': len(df[df['pnl'] > 0]),
                'losing_trades': len(df[df['pnl'] < 0]),
                'total_pnl': df['pnl'].sum() if 'pnl' in df else 0,
                'win_rate': len(df[df['pnl'] > 0]) / len(df) * 100 if len(df) > 0 else 0
            }
        except:
            return {'total_trades': 0}

if __name__ == "__main__":
    logger = TradeLogger()
    test = {'timestamp': datetime.now().isoformat(), 'type': 'BUY', 'price': 3000, 'quantity': 0.001, 'order_id': '123'}
    logger.log_trade(test)
    print(logger.get_trade_history())
