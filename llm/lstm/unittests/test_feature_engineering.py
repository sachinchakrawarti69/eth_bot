import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.load_data import load_ohlcv
from llm.lstm.preprocessing.clean_data import clean_ohlcv
from llm.lstm.preprocessing.technical_indicators import add_all_indicators
from llm.lstm.preprocessing.feature_engineering import add_all_features


print("=" * 70)
print("TEST FEATURE ENGINEERING")
print("=" * 70)

# ==========================================================
# Load
# ==========================================================

df = load_ohlcv()

print("\nOriginal Shape")
print(df.shape)

# ==========================================================
# Clean
# ==========================================================

df = clean_ohlcv(df)

print("\nAfter Cleaning")
print(df.shape)

# ==========================================================
# Technical Indicators
# ==========================================================

df = add_all_indicators(df)

print("\nAfter Technical Indicators")
print(df.shape)

# ==========================================================
# Feature Engineering
# ==========================================================

df = add_all_features(df)

print("\nAfter Feature Engineering")
print(df.shape)

print("\nColumns")

print(df.columns.tolist())

print("\nData Types")

print(df.dtypes)

print("\nMissing Values")

print(df.isnull().sum())

print("\nLast 10 Rows")

print(df.tail(10))

print("\nDataFrame Info")

print(df.info())

print("\n")

print("=" * 70)
print("FEATURE ENGINEERING TEST PASSED")
print("=" * 70)