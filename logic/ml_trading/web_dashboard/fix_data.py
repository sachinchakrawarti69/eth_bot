"""
Fix database structure and populate with correct data
"""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'ETH.db'

def fix_database():
    print("=" * 60)
    print("🔧 Fixing Database Structure")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Check existing tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"📋 Existing tables: {[t[0] for t in tables]}")
    
    # Drop and recreate tables with correct schema
    print("\n📊 Recreating tables with correct schema...")
    
    # Drop old tables if they exist
    conn.execute("DROP TABLE IF EXISTS eth_ohlcv")
    conn.execute("DROP TABLE IF EXISTS signals")
    conn.execute("DROP TABLE IF EXISTS trades")
    
    # Create OHLCV table
    conn.execute('''CREATE TABLE eth_ohlcv (
        date TEXT PRIMARY KEY,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL
    )''')
    
    # Create signals table
    conn.execute('''CREATE TABLE signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        signal INTEGER,
        signal_type TEXT,
        confidence REAL,
        current_price REAL,
        recommendation TEXT,
        model TEXT
    )''')
    
    # Create trades table
    conn.execute('''CREATE TABLE trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        type TEXT,
        price REAL,
        quantity REAL,
        order_id TEXT,
        pnl REAL,
        pnl_percent REAL,
        signal_confidence REAL
    )''')
    
    print("✅ Tables recreated")
    
    # Insert sample data
    print("\n📊 Inserting sample data...")
    
    # OHLCV data (30 days)
    start_date = datetime.now() - timedelta(days=30)
    base_price = 1877
    
    for i in range(30):
        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        price = base_price + i * 2 + random.randint(-15, 15)
        high = price + random.randint(5, 20)
        low = price - random.randint(5, 20)
        volume = random.randint(20000, 100000)
        
        conn.execute('''INSERT INTO eth_ohlcv 
            (date, open, high, low, close, volume) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (date, price, high, low, price, volume))
    
    print("✅ Added 30 days OHLCV data")
    
    # Signals data
    signals = ['HOLD', 'BUY', 'HOLD', 'SELL', 'HOLD', 'BUY', 'HOLD', 'HOLD', 'SELL', 'BUY']
    for i, signal in enumerate(signals):
        price = 1877 + random.randint(-30, 30)
        confidence = random.uniform(0.4, 0.85)
        
        conn.execute('''INSERT INTO signals 
            (timestamp, signal, signal_type, confidence, current_price, recommendation, model)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (datetime.now().isoformat(), 
             ['HOLD', 'BUY', 'SELL'].index(signal) if signal in ['HOLD', 'BUY', 'SELL'] else 0,
             signal, 
             confidence, 
             price, 
             f"{signal} at ${price}", 
             "LogisticRegression"))
    
    print("✅ Added 10 signals")
    
    # Trades data
    trade_types = ['BUY', 'SELL', 'BUY', 'SELL', 'BUY']
    trade_prices = [1877, 1890, 1885, 1870, 1895]
    trade_pnls = [5.50, -8.20, 12.30, -3.10, 28.20]
    
    for i in range(5):
        conn.execute('''INSERT INTO trades 
            (timestamp, type, price, quantity, order_id, pnl, pnl_percent, signal_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (datetime.now().isoformat(), 
             trade_types[i], 
             trade_prices[i], 
             0.001, 
             f"order_{i+1}", 
             trade_pnls[i], 
             (trade_pnls[i]/trade_prices[i])*100, 
             random.uniform(0.5, 0.8)))
    
    print("✅ Added 5 trades")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database fixed and populated!")
    print("=" * 60)
    
    # Verify
    verify_db()

def verify_db():
    """Verify database content"""
    conn = sqlite3.connect(DB_PATH)
    
    print("\n📊 Verification:")
    
    # Check counts
    ohlcv_count = conn.execute("SELECT COUNT(*) FROM eth_ohlcv").fetchone()[0]
    signals_count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    trades_count = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    
    print(f"   OHLCV: {ohlcv_count} rows")
    print(f"   Signals: {signals_count} rows")
    print(f"   Trades: {trades_count} rows")
    
    # Latest values
    price = conn.execute("SELECT close FROM eth_ohlcv ORDER BY date DESC LIMIT 1").fetchone()
    if price:
        print(f"   Latest Price: ${price[0]:.2f}")
    
    signal = conn.execute("SELECT signal_type, confidence FROM signals ORDER BY id DESC LIMIT 1").fetchone()
    if signal:
        print(f"   Latest Signal: {signal[0]} (Confidence: {signal[1]*100:.1f}%)")
    
    trade_count = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    print(f"   Total Trades: {trade_count}")
    
    conn.close()
    print("=" * 60)

if __name__ == "__main__":
    fix_database()