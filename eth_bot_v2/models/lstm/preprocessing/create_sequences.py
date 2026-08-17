import numpy as np
import pandas as pd


# ==========================================================
# Prepare Numeric Data
# ==========================================================

def prepare_numeric_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only numeric columns for LSTM.
    """

    df = df.copy()

    df = df.dropna()

    df = df.reset_index(drop=True)

    numeric_df = df.select_dtypes(include=["number"])

    return numeric_df


# ==========================================================
# Create Sequences
# ==========================================================

def create_sequences(
    df: pd.DataFrame,
    sequence_length: int = 60,
    target_column: str = "close",
):
    """
    Convert DataFrame into LSTM sequences.

    Returns
    -------
    X : (samples, timesteps, features)

    y : (samples,)
    """

    df = prepare_numeric_dataframe(df)

    if target_column not in df.columns:
        raise ValueError(
            f"Target column '{target_column}' not found."
        )

    feature_columns = df.columns.tolist()

    target_index = feature_columns.index(target_column)

    data = df.to_numpy(dtype=np.float32)

    X = []
    y = []

    for i in range(len(data) - sequence_length):

        X.append(
            data[i:i + sequence_length]
        )

        y.append(
            data[i + sequence_length][target_index]
        )

    X = np.array(X, dtype=np.float32)

    y = np.array(y, dtype=np.float32)

    return X, y


# ==========================================================
# Dataset Information
# ==========================================================

def print_sequence_info(X, y):

    print("=" * 60)
    print("LSTM DATASET")
    print("=" * 60)

    print("Samples   :", X.shape[0])
    print("Timesteps :", X.shape[1])
    print("Features  :", X.shape[2])

    print()

    print("Target Shape :", y.shape)


# ==========================================================
# Train/Test Split
# ==========================================================

def split_sequences(
    X,
    y,
    train_ratio=0.80,
):

    split = int(len(X) * train_ratio)

    X_train = X[:split]
    y_train = y[:split]

    X_test = X[split:]
    y_test = y[split:]

    return (
        X_train,
        X_test,
        y_train,
        y_test,
    )


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    print("create_sequences.py loaded successfully.")