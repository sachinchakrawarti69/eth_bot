import numpy as np
import pandas as pd


# ==========================================================
# Returns
# ==========================================================

def add_returns(df: pd.DataFrame) -> pd.DataFrame:

    df["return"] = df["close"].pct_change()

    df["log_return"] = np.log(df["close"] / df["close"].shift(1))

    return df


# ==========================================================
# Price Change
# ==========================================================

def add_price_change(df):

    df["price_change"] = df["close"] - df["open"]

    df["price_change_percent"] = (
        (df["close"] - df["open"]) / df["open"]
    ) * 100

    return df


# ==========================================================
# Candle Features
# ==========================================================

def add_candle_features(df):

    df["body_size"] = abs(df["close"] - df["open"])

    df["upper_shadow"] = df["high"] - df[["open", "close"]].max(axis=1)

    df["lower_shadow"] = df[["open", "close"]].min(axis=1) - df["low"]

    df["candle_range"] = df["high"] - df["low"]

    return df


# ==========================================================
# Rolling Statistics
# ==========================================================

def add_rolling_statistics(df):

    df["rolling_mean_10"] = df["close"].rolling(10).mean()

    df["rolling_std_10"] = df["close"].rolling(10).std()

    df["rolling_max_10"] = df["close"].rolling(10).max()

    df["rolling_min_10"] = df["close"].rolling(10).min()

    return df


# ==========================================================
# Lag Features
# ==========================================================

def add_lag_features(df):

    for lag in [1, 2, 3, 5, 10]:

        df[f"close_lag_{lag}"] = df["close"].shift(lag)

        df[f"volume_lag_{lag}"] = df["volume"].shift(lag)

    return df


# ==========================================================
# Volume Features
# ==========================================================

def add_volume_features(df):

    df["volume_change"] = df["volume"].pct_change()

    df["volume_ma_10"] = df["volume"].rolling(10).mean()

    return df


# ==========================================================
# Volatility
# ==========================================================

def add_volatility(df):

    df["volatility_10"] = df["return"].rolling(10).std()

    return df


# ==========================================================
# Complete Pipeline
# ==========================================================

def add_all_features(df):

    df = add_returns(df)

    df = add_price_change(df)

    df = add_candle_features(df)

    df = add_rolling_statistics(df)

    df = add_lag_features(df)

    df = add_volume_features(df)

    df = add_volatility(df)

    return df