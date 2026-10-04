"""Technical indicators."""
import pandas as pd


def sma(s, n): return s.rolling(n).mean()
def ema(s, n): return s.ewm(span=n, adjust=False).mean()


def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, pd.NA))


def macd(close, fast=12, slow=26, signal=9):
    line = ema(close, fast) - ema(close, slow)
    sig  = ema(line, signal)
    return line, sig, line - sig


def atr(df, n=14):
    tr = pd.concat([
        df.high - df.low,
        (df.high - df.close.shift()).abs(),
        (df.low  - df.close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def add_all(df):
    df = df.copy()
    df["sma_50"]  = sma(df.close, 50)
    df["sma_200"] = sma(df.close, 200)
    df["ema_12"]  = ema(df.close, 12)
    df["ema_26"]  = ema(df.close, 26)
    df["rsi_14"]  = rsi(df.close, 14)
    df["macd"], df["macd_sig"], df["macd_hist"] = macd(df.close)
    df["atr_14"]  = atr(df, 14)
    return df
