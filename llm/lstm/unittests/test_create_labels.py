import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.load_data import load_ohlcv
from llm.lstm.preprocessing.clean_data import clean_ohlcv
from llm.lstm.preprocessing.technical_indicators import add_all_indicators
from llm.lstm.preprocessing.feature_engineering import add_all_features

from llm.lstm.preprocessing.create_labels import (
    create_next_close_label,
    create_direction_label,
    create_return_label,
    create_multiclass_label,
    align_dataset,
)

print("=" * 70)
print("TEST CREATE LABELS")
print("=" * 70)

# ----------------------------------------------------------
# Load Data
# ----------------------------------------------------------

df = load_ohlcv()

print("\nOriginal Shape")
print(df.shape)

# ----------------------------------------------------------
# Clean
# ----------------------------------------------------------

df = clean_ohlcv(df)

# ----------------------------------------------------------
# Indicators
# ----------------------------------------------------------

df = add_all_indicators(df)

# ----------------------------------------------------------
# Features
# ----------------------------------------------------------

df = add_all_features(df)

df = df.dropna().reset_index(drop=True)

print("\nFeature Shape")
print(df.shape)

# ----------------------------------------------------------
# Next Close
# ----------------------------------------------------------

next_close = create_next_close_label(df)

# ----------------------------------------------------------
# Direction
# ----------------------------------------------------------

direction = create_direction_label(df)

# ----------------------------------------------------------
# Return
# ----------------------------------------------------------

returns = create_return_label(df)

# ----------------------------------------------------------
# Multi-Class
# ----------------------------------------------------------

multiclass = create_multiclass_label(df)

# ----------------------------------------------------------
# Align
# ----------------------------------------------------------

aligned_df, aligned_labels = align_dataset(df, next_close)

print("\nAligned Shape")
print(aligned_df.shape)
print(aligned_labels.shape)

print("\nNext Close")
print(next_close.head())

print("\nDirection")
print(direction.value_counts())

print("\nReturn")
print(returns.head())

print("\nMulti Class")
print(multiclass.value_counts())

print("\nLast 5 Labels")
print(aligned_labels.tail())

print("\nDataFrame Info")
print(aligned_df.info())

print("\n")
print("=" * 70)
print("CREATE LABELS TEST PASSED")
print("=" * 70)

