import pandas as pd

from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
)


# ==========================================================
# Numeric Columns
# ==========================================================

def get_numeric_columns(df: pd.DataFrame):

    return df.select_dtypes(include=["number"]).columns.tolist()


# ==========================================================
# Standard Scaler
# ==========================================================

def standard_scale(df: pd.DataFrame):

    df = df.copy()

    scaler = StandardScaler()

    columns = get_numeric_columns(df)

    df[columns] = scaler.fit_transform(df[columns])

    return df, scaler


# ==========================================================
# MinMax Scaler
# ==========================================================

def minmax_scale(df: pd.DataFrame):

    df = df.copy()

    scaler = MinMaxScaler()

    columns = get_numeric_columns(df)

    df[columns] = scaler.fit_transform(df[columns])

    return df, scaler


# ==========================================================
# Robust Scaler
# ==========================================================

def robust_scale(df: pd.DataFrame):

    df = df.copy()

    scaler = RobustScaler()

    columns = get_numeric_columns(df)

    df[columns] = scaler.fit_transform(df[columns])

    return df, scaler


# ==========================================================
# Normalize Pipeline
# ==========================================================

def normalize(df: pd.DataFrame,
              method="standard"):

    if method == "standard":
        return standard_scale(df)

    if method == "minmax":
        return minmax_scale(df)

    if method == "robust":
        return robust_scale(df)

    raise ValueError("Unknown normalization method.")