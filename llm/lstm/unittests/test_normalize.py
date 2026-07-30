import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.load_data import load_ohlcv
from llm.lstm.preprocessing.clean_data import clean_ohlcv
from llm.lstm.preprocessing.technical_indicators import add_all_indicators
from llm.lstm.preprocessing.feature_engineering import add_all_features
from llm.lstm.preprocessing.normalize import normalize


print("=" * 70)
print("TEST NORMALIZATION")
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

# ==========================================================
# Indicators
# ==========================================================

df = add_all_indicators(df)

# ==========================================================
# Features
# ==========================================================

df = add_all_features(df)

print("\nBefore Normalization")
print(df.shape)

# ==========================================================
# Remove NaN created by rolling windows
# ==========================================================

df = df.dropna().reset_index(drop=True)

print("\nAfter Drop NA")
print(df.shape)

# ==========================================================
# Standard
# ==========================================================

scaled_df, scaler = normalize(df, method="standard")

print("\nStandard Scaling")
print("-" * 70)

print(scaled_df.head())

# ==========================================================
# Statistics
# ==========================================================

numeric = scaled_df.select_dtypes(include="number")

print("\nMean")
print("-" * 70)
print(numeric.mean().head(20))

print("\nStd")
print("-" * 70)
print(numeric.std().head(20))

print("\nShape")
print("-" * 70)
print(scaled_df.shape)

print("\nColumns")
print("-" * 70)
print(scaled_df.columns.tolist())

print("\nData Types")
print("-" * 70)
print(scaled_df.dtypes)

print("\nInfo")
print("-" * 70)
print(scaled_df.info())

print("\n")
print("=" * 70)
print("NORMALIZATION TEST PASSED")
print("=" * 70)