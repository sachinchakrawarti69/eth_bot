import numpy as np
import pandas as pd


# ==========================================================
# Next Close Price
# ==========================================================

def create_next_close_label(
    df: pd.DataFrame,
    target_column: str = "close",
):
    """
    Predict next candle close price.
    """

    if target_column not in df.columns:
        raise ValueError(f"{target_column} not found.")

    labels = df[target_column].shift(-1)

    return labels


# ==========================================================
# Binary Direction
# ==========================================================

def create_direction_label(
    df: pd.DataFrame,
    target_column: str = "close",
):
    """
    1 = Price Up
    0 = Price Down
    """

    future = df[target_column].shift(-1)

    labels = np.where(
        future > df[target_column],
        1,
        0,
    )

    return pd.Series(labels)


# ==========================================================
# Percentage Return
# ==========================================================

def create_return_label(
    df: pd.DataFrame,
    target_column: str = "close",
):
    """
    Predict next candle return.
    """

    labels = (
        df[target_column].shift(-1)
        - df[target_column]
    ) / df[target_column]

    return labels


# ==========================================================
# Multi Class
# ==========================================================

def create_multiclass_label(
    df: pd.DataFrame,
    threshold=0.01,
    target_column="close",
):
    """
    0 = Sell
    1 = Hold
    2 = Buy
    """

    future_return = (
        df[target_column].shift(-1)
        - df[target_column]
    ) / df[target_column]

    labels = []

    for value in future_return:

        if pd.isna(value):
            labels.append(np.nan)

        elif value > threshold:
            labels.append(2)

        elif value < -threshold:
            labels.append(0)

        else:
            labels.append(1)

    return pd.Series(labels)


# ==========================================================
# Remove Last Row
# ==========================================================

def align_dataset(df, labels):

    df = df.iloc[:-1].reset_index(drop=True)

    labels = labels.iloc[:-1].reset_index(drop=True)

    return df, labels