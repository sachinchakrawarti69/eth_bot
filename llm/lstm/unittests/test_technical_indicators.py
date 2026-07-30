import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.load_data import load_ohlcv
from llm.lstm.preprocessing.clean_data import clean_ohlcv
from llm.lstm.preprocessing.technical_indicators import add_all_indicators


print("=" * 70)
print("TEST TECHNICAL INDICATORS")
print("=" * 70)

# ==========================================================
# Load Data
# ==========================================================

df = load_ohlcv()

print("\nOriginal Data")
print("-" * 70)
print("Shape :", df.shape)

# ==========================================================
# Clean Data
# ==========================================================

df = clean_ohlcv(df)

print("\nAfter Cleaning")
print("-" * 70)
print("Shape :", df.shape)

# ==========================================================
# Add Indicators
# ==========================================================

df = add_all_indicators(df)

print("\nAfter Technical Indicators")
print("-" * 70)
print("Shape :", df.shape)

# ==========================================================
# Indicator Columns
# ==========================================================

indicator_columns = [
    "sma_20",
    "sma_50",
    "sma_100",
    "ema_20",
    "ema_50",
    "rsi",
    "macd",
    "macd_signal",
    "macd_histogram",
    "bb_high",
    "bb_middle",
    "bb_low",
    "atr",
    "obv",
]

print("\nIndicator Columns")
print("-" * 70)

for column in indicator_columns:

    if column in df.columns:
        print(f"✓ {column}")
    else:
        print(f"✗ {column}")

# ==========================================================
# Data Types
# ==========================================================

print("\nData Types")
print("-" * 70)
print(df.dtypes)

# ==========================================================
# Missing Values
# ==========================================================

print("\nMissing Values")
print("-" * 70)
print(df[indicator_columns].isnull().sum())

# ==========================================================
# Last Rows
# ==========================================================

print("\nLast 10 Rows")
print("-" * 70)
print(df.tail(10))

# ==========================================================
# Data Info
# ==========================================================

print("\nDataFrame Info")
print("-" * 70)
print(df.info())

print("\n")
print("=" * 70)
print("TECHNICAL INDICATORS TEST PASSED")
print("=" * 70)