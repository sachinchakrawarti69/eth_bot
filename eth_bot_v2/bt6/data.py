"""Load 6 years of daily features + candles."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"


def load_daily(symbol="ETHUSDT"):
    """Return daily OHLCV + indicators from the ohlcv table.

    This uses the ohlcv table directly (6 years of 1d bars)
    because the features table only has ~2 years of 1h rows.
    """
    with sqlite3.connect(DB_PATH) as c:
        df = pd.read_sql_query(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlcv WHERE symbol=? AND timeframe='1d' "
            "ORDER BY open_time",
            c, params=(symbol,))
    if df.empty:
        raise RuntimeError("no daily ohlcv for " + symbol)

    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.drop(columns=["open_time"]).set_index("date")

    # indicators
    df["ret_1"]  = df["close"].pct_change()
    df["ret_5"]  = df["close"].pct_change(5)
    df["ret_20"] = df["close"].pct_change(20)
    df["vol_20"] = df["ret_1"].rolling(20).std()
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["sma_200"]= df["close"].rolling(200).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()
    macd = df["ema_12"] - df["ema_26"]
    df["macd"]      = macd
    df["macd_sig"]  = macd.ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

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

    df["trend_up"]   = ((df["close"] > df["sma_50"]) & (df["sma_50"] > df["sma_200"])).astype(int)
    df["trend_down"] = ((df["close"] < df["sma_50"]) & (df["sma_50"] < df["sma_200"])).astype(int)

    def regime(row):
        if row["trend_up"] == 1:   return "bull"
        if row["trend_down"] == 1: return "bear"
        return "chop"

    df["regime"] = df.apply(regime, axis=1)
    df["dist_sma50"] = (df["close"] - df["sma_50"]) / df["sma_50"]

    return df.dropna(subset=["sma_200"])
