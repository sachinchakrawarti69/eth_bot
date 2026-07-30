"""
Multi-timeframe analysis
"""
import pandas as pd
import sqlite3
from pathlib import Path

db_path = Path('..') / 'data' / 'ETH.db'

def get_multi_timeframe_signals():
    """Get signals from multiple timeframes"""
    conn = sqlite3.connect(db_path)
    
    # Daily data
    daily = pd.read_sql("SELECT * FROM eth_ohlcv ORDER BY date", conn, parse_dates=['date'])
    
    # Create weekly data
    weekly = daily.resample('W', on='date').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    # Create monthly data
    monthly = daily.resample('M', on='date').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    # Get latest values
    daily_trend = daily['close'].iloc[-1] - daily['close'].iloc[-30]
    weekly_trend = weekly['close'].iloc[-1] - weekly['close'].iloc[-4] if len(weekly) > 4 else 0
    monthly_trend = monthly['close'].iloc[-1] - monthly['close'].iloc[-2] if len(monthly) > 2 else 0
    
    # Generate signal
    signal = "HOLD"
    confidence = 0
    
    if daily_trend > 0 and weekly_trend > 0:
        signal = "BUY"
        confidence = 0.65
    elif daily_trend < 0 and weekly_trend < 0:
        signal = "SELL"
        confidence = 0.65
    elif daily_trend > 0 and monthly_trend > 0:
        signal = "BUY"
        confidence = 0.55
    elif daily_trend < 0 and monthly_trend < 0:
        signal = "SELL"
        confidence = 0.55
    
    return {
        'signal': signal,
        'confidence': confidence,
        'daily_trend': daily_trend,
        'weekly_trend': weekly_trend,
        'monthly_trend': monthly_trend
    }

if __name__ == "__main__":
    result = get_multi_timeframe_signals()
    print("📊 Multi-Timeframe Analysis")
    print("=" * 40)
    print(f"Daily Trend: ${result['daily_trend']:.2f}")
    print(f"Weekly Trend: ${result['weekly_trend']:.2f}")
    print(f"Monthly Trend: ${result['monthly_trend']:.2f}")
    print(f"Signal: {result['signal']} (Conf: {result['confidence']*100:.1f}%)")