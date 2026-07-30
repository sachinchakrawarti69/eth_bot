"""
Data preparation for ML models
"""
import pandas as pd
import sqlite3
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from server.notebooks.ml_trading.config import DB_PATH, FEATURES

def load_data_from_sqlite():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM eth_ohlcv ORDER BY date", conn, parse_dates=['date'])
        conn.close()
        print(f"Loaded {len(df)} days of data from SQLite")
        return df
    except:
        csv_path = Path(__file__).parent.parent / 'data' / 'Eth_OHLCV.csv'
        if csv_path.exists():
            df = pd.read_csv(csv_path, parse_dates=['date'])
            print(f"Loaded {len(df)} days of data from CSV")
            return df
        print("No data found")
        return None

def add_technical_indicators(df):
    if df is None or len(df) == 0:
        return None
    df = df.copy()
    df['SMA_7'] = df['close'].rolling(7).mean()
    df['SMA_20'] = df['close'].rolling(20).mean()
    df['SMA_50'] = df['close'].rolling(50).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['BB_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR_14'] = true_range.rolling(14).mean()
    return df

def create_target_variable(df, days_ahead=1):
    if df is None or len(df) == 0:
        return None
    df = df.copy()
    df['future_close'] = df['close'].shift(-days_ahead)
    df['target'] = df['future_close'] / df['close'] - 1
    df['target_class'] = 0
    df.loc[df['target'] > 0.01, 'target_class'] = 1
    df.loc[df['target'] < -0.01, 'target_class'] = 2
    return df

def prepare_ml_data(df):
    if df is None:
        return None, None, None, None, None
    df = add_technical_indicators(df)
    df = create_target_variable(df)
    df = df.dropna()
    if len(df) < 100:
        print("Not enough data for ML")
        return None, None, None, None, None
    X = df[FEATURES]
    y = df['target_class']
    split_idx = int(len(df) * 0.8)
    X_train = X[:split_idx]
    X_test = X[split_idx:]
    y_train = y[:split_idx]
    y_test = y[split_idx:]
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    return X_train, X_test, y_train, y_test, df

def get_latest_data_for_prediction():
    df = load_data_from_sqlite()
    if df is None:
        return None, None
    df = add_technical_indicators(df)
    df = df.dropna()
    latest = df[FEATURES].iloc[-1:].values.reshape(1, -1)
    return latest, df
