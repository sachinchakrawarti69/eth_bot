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
)

from llm.lstm.preprocessing.split_dataset import (
    split_dataset,
    print_dataset_summary,
    verify_split,
)

print("=" * 70)
print("TEST SPLIT DATASET")
print("=" * 70)

# ----------------------------------------------------------
# Load
# ----------------------------------------------------------

df = load_ohlcv()

df = clean_ohlcv(df)

df = add_all_indicators(df)

df = add_all_features(df)

df = df.dropna().reset_index(drop=True)

df, scaler = normalize(df)

# ----------------------------------------------------------
# Create Sequences
# ----------------------------------------------------------

X, y = create_sequences(
    df,
    sequence_length=60,
    target_column="close",
)

print()

print("Sequence Shape")

print("X :", X.shape)

print("y :", y.shape)

# ----------------------------------------------------------
# Split
# ----------------------------------------------------------

(
    X_train,
    X_validation,
    X_test,
    y_train,
    y_validation,
    y_test,
) = split_dataset(
    X,
    y,
)

# ----------------------------------------------------------
# Summary
# ----------------------------------------------------------

print_dataset_summary(
    X_train,
    X_validation,
    X_test,
    y_train,
    y_validation,
    y_test,
)

# ----------------------------------------------------------
# Verify
# ----------------------------------------------------------

verify_split(
    X_train,
    X_validation,
    X_test,
)

print()

print("=" * 70)
print("FIRST TARGET VALUES")
print("=" * 70)

print("Train      :", y_train[:5])

print()

print("Validation :", y_validation[:5])

print()

print("Test       :", y_test[:5])

print()

print("=" * 70)
print("TEST PASSED")
print("=" * 70)