"""
Populate database with sample data for dashboard testing
"""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'ETH.db'

def populate_sample_data():
    """Insert sample data for testing"""
    print("📊 Populating database with sample data...")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Clear existing data (optional)
    # conn.execute("DELETE FROM eth_ohlcv")
    # conn.execute("DELETE FROM signals")
    # conn.execute("DELETE FROM trades")
    
    # 1. Sample OHLCV data (30 days)
    print("📈 Creating sample OHLCV data...")
    start_date = datetime.now() - timedelta(days=30)
    base_price = 1800
    
    for i in range(30):
        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        price = base_price + i * 2 + random.randint(-20, 20)
        high = price + random.randint(5, 15)
        low = price - random.randint(5, 15)
        volume = random.randint(10000, 80000)
        
        conn.execute('''INSERT OR REPLACE INTO eth_ohlcv 
            (date, open, high, low, close, volume) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (date, price, high, low, price, volume))
    
    print(f"✅ Added 30 days of OHLCV data")
    
    # 2. Sample signals
    print("📊 Creating sample signals...")
    signal_types = ['BUY', 'SELL', 'HOLD']
    for i in range(10):
        signal = random.choice(signal_types)
        confidence = random.uniform(0.3, 0.85)
        price = 1800 + random.randint(-50, 50)
        
        conn.execute('''INSERT INTO signals 
            (timestamp, signal, signal_type, confidence, current_price, recommendation, model)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (datetime.now().isoformat(), 
             signal_types.index(signal), 
             signal, 
             confidence, 
             price, 
             f"{signal} at ${price}", 
             "LogisticRegression"))
    
    print(f"✅ Added 10 signals")
    
    # 3. Sample trades
    print("💰 Creating sample trades...")
    trade_types = ['BUY', 'SELL']
    for i in range(5):
        trade_type = random.choice(trade_types)
        price = 1800 + random.randint(-30, 30)
        quantity = 0.001
        pnl = random.uniform(-5, 10)
        
        conn.execute('''INSERT INTO trades 
            (timestamp, type, price, quantity, order_id, pnl, pnl_percent, signal_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (datetime.now().isoformat(), 
             trade_type, 
             price, 
             quantity, 
             f"order_{i}", 
             pnl, 
             (pnl/price)*100, 
             random.uniform(0.4, 0.8)))
    
    print(f"✅ Added 5 trades")
    
    conn.commit()
    conn.close()
    print("🎉 Database populated successfully!")
    print(f"📁 Location: {DB_PATH}")

if __name__ == "__main__":
    populate_sample_data()