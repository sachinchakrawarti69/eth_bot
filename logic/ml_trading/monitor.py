import sqlite3
from pathlib import Path
import time
import os

db_path = Path('..') / 'data' / 'ETH.db'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def monitor():
    while True:
        clear_screen()
        print("=" * 60)
        print("📊 ETH Trading Bot Monitor")
        print("=" * 60)
        
        conn = sqlite3.connect(db_path)
        
        # Get latest signal
        signal = conn.execute("SELECT timestamp, signal_type, current_price, confidence FROM signals ORDER BY id DESC LIMIT 1").fetchone()
        if signal:
            print(f"\n📈 Latest Signal: {signal[1]}")
            print(f"💰 Price: ${signal[2]:.2f}")
            print(f"📊 Confidence: {signal[3]*100:.1f}%")
            print(f"🕐 Time: {signal[0]}")
        
        # Get trade count
        trade_count = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        print(f"\n💼 Total Trades: {trade_count}")
        
        # Get performance
        try:
            pnl = conn.execute("SELECT SUM(pnl) FROM trades").fetchone()[0]
            if pnl:
                print(f"💰 Total P&L: ${pnl:.2f}")
        except:
            pass
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("Press Ctrl+C to exit")
        time.sleep(5)

if __name__ == "__main__":
    monitor()