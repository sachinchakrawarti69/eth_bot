import pandas as pd
import ta


# ==========================================================
# Trend Indicators
# ==========================================================

def add_sma(df: pd.DataFrame) -> pd.DataFrame:

    df["sma_20"] = ta.trend.sma_indicator(
        close=df["close"],
        window=20
    )

    df["sma_50"] = ta.trend.sma_indicator(
        close=df["close"],
        window=50
    )

    df["sma_100"] = ta.trend.sma_indicator(
        close=df["close"],
        window=100
    )

    return df


def add_ema(df: pd.DataFrame) -> pd.DataFrame:

    df["ema_20"] = ta.trend.ema_indicator(
        close=df["close"],
        window=20
    )

    df["ema_50"] = ta.trend.ema_indicator(
        close=df["close"],
        window=50
    )

    return df


# ==========================================================
# Momentum
# ==========================================================

def add_rsi(df):

    df["rsi"] = ta.momentum.rsi(
        close=df["close"],
        window=14
    )

    return df


def add_macd(df):

    indicator = ta.trend.MACD(df["close"])

    df["macd"] = indicator.macd()

    df["macd_signal"] = indicator.macd_signal()

    df["macd_histogram"] = indicator.macd_diff()

    return df


# ==========================================================
# Volatility
# ==========================================================

def add_bollinger(df):

    indicator = ta.volatility.BollingerBands(df["close"])

    df["bb_high"] = indicator.bollinger_hband()

    df["bb_middle"] = indicator.bollinger_mavg()

    df["bb_low"] = indicator.bollinger_lband()

    return df


def add_atr(df):

    indicator = ta.volatility.AverageTrueRange(

        high=df["high"],
        low=df["low"],
        close=df["close"]

    )

    df["atr"] = indicator.average_true_range()

    return df


# ==========================================================
# Volume
# ==========================================================

def add_obv(df):

    df["obv"] = ta.volume.on_balance_volume(

        close=df["close"],
        volume=df["volume"]

    )

    return df


# ==========================================================
# Complete Pipeline
# ==========================================================

def add_all_indicators(df):

    df = add_sma(df)

    df = add_ema(df)

    df = add_rsi(df)

    df = add_macd(df)

    df = add_bollinger(df)

    df = add_atr(df)

    df = add_obv(df)

    return df