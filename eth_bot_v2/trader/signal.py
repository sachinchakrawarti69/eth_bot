"""Generate today's live trade signal."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"


def load_daily(symbol):
    with sqlite3.connect(DB_PATH) as c:
        df = pd.read_sql_query(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlcv WHERE symbol=? AND timeframe='1d' "
            "ORDER BY open_time",
            c, params=(symbol,))
    if df.empty:
        raise RuntimeError("no daily data for " + symbol)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.drop(columns=["open_time"]).set_index("date")
    return df


def add_indicators(df):
    df = df.copy()
    df["sma_50"]  = df["close"].rolling(50).mean()
    df["sma_200"] = df["close"].rolling(200).mean()
    df["ema_12"]  = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"]  = df["close"].ewm(span=26, adjust=False).mean()
    macd = df["ema_12"] - df["ema_26"]
    df["macd_hist"] = macd - macd.ewm(span=9, adjust=False).mean()

    d  = df["close"].diff()
    up = d.clip(lower=0).rolling(14).mean()
    dn = (-d.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - 100 / (1 + up / dn.replace(0, float("nan")))

    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"]  - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()

    df["bull"] = (df["close"] > df["sma_50"]) & (df["sma_50"] > df["sma_200"])
    return df.dropna()


def current_signal(symbol):
    df = load_daily(symbol)
    df = add_indicators(df)
    if df.empty:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    bull      = bool(last["bull"])
    macd_hist = float(last["macd_hist"])
    prev_macd = float(prev["macd_hist"])

    if bull and macd_hist > 0 and prev_macd <= 0:
        action = "BUY"
        reason = "bull trend + MACD turned positive"
    elif bull and macd_hist > 0:
        action = "HOLD"
        reason = "bull trend + MACD positive"
    elif not bull and macd_hist < 0:
        action = "EXIT"
        reason = "trend broke + MACD negative"
    else:
        action = "WAIT"
        reason = "conditions not met"

    return {
        "symbol":    symbol,
        "date":      df.index[-1].date().isoformat(),
        "price":     float(last["close"]),
        "action":    action,
        "reason":    reason,
        "bull":      bull,
        "macd_hist": macd_hist,
        "rsi_14":    float(last["rsi_14"]),
        "sma_50":    float(last["sma_50"]),
        "sma_200":   float(last["sma_200"]),
        "atr_14":    float(last["atr_14"]),
    }
