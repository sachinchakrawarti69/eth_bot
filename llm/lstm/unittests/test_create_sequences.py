import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.load_data import load_ohlcv
from llm.lstm.preprocessing.clean_data import clean_ohlcv
from llm.lstm.preprocessing.technical_indicators import add_all_indicators
from llm.lstm.preprocessing.feature_engineering import add_all_features
from llm.lstm.preprocessing.normalize import normalize

from llm.lstm.preprocessing.create_sequences import (
    create_sequences,
    split_sequences,
    print_sequence_info,
)


print("=" * 70)
print("TEST CREATE SEQUENCES")
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

# ==========================================================
# Normalize
# ==========================================================

df, scaler = normalize(df)

print("\nAfter Normalization")
print(df.shape)

# ==========================================================
# Numeric Columns Only
# ==========================================================

numeric_df = df.select_dtypes(include=["number"])

print("\nNumeric Shape")
print(numeric_df.shape)

print("\nNumeric Columns")
print(numeric_df.columns.tolist())

# ==========================================================
# Create Sequences
# ==========================================================

X, y = create_sequences(
    numeric_df,
    sequence_length=60,
    target_column="close",
)

print()

print_sequence_info(X, y)

# ==========================================================
# Split Dataset
# ==========================================================

X_train, X_test, y_train, y_test = split_sequences(
    X,
    y,
)

print()

print("=" * 70)
print("TRAIN SET")
print("=" * 70)

print("X_train :", X_train.shape)
print("y_train :", y_train.shape)

print()

print("=" * 70)
print("TEST SET")
print("=" * 70)

print("X_test :", X_test.shape)
print("y_test :", y_test.shape)

print()

print("=" * 70)
print("FIRST SAMPLE")
print("=" * 70)

print(X_train[0])

print()

print("=" * 70)
print("FIRST TARGET")
print("=" * 70)

print(y_train[0])

print()

print("=" * 70)
print("TEST PASSED")
print("=" * 70)