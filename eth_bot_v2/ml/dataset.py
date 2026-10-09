"""Build X (features) and y (labels) from the features table."""

from __future__ import annotations
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"


FEATURES = [
    "ret_1", "ret_5", "ret_20", "vol_20",
    "rsi_14", "macd_hist", "atr_14",
    "sma_20", "sma_50", "sma_200",
    "ema_12", "ema_26",
    "rsi_14_4h", "macd_hist_4h",
    "rsi_14_1d", "sma_50_1d", "sma_200_1d",
    "funding", "oi_chg_24h", "ls_ratio", "taker_ratio",
    "trend_up", "trend_down",
    "dist_sma50", "dist_sma200", "dist_sma50_1d",
    "hour", "weekday",
]


def load(symbol="ETHUSDT"):
    with sqlite3.connect(DB_PATH) as c:
        df = pd.read_sql_query(
            "SELECT * FROM features WHERE symbol=? ORDER BY ts",
            c, params=(symbol,))
    return df


def build(symbol="ETHUSDT"):
    df = load(symbol)
    if df.empty:
        raise RuntimeError("no features for " + symbol)

    df = df[df["dir_24h"].notna()].copy()

    regime_map = {"bull": 2, "chop": 1, "bear": 0}
    df["regime_enc"] = df["regime"].map(regime_map).fillna(1).astype(int)

    features = FEATURES + ["regime_enc"]

    # keep only columns with at least 20% coverage
    coverage = df[features].notna().mean()
    keep = coverage[coverage > 0.2].index.tolist()

    X = df[keep].copy()
    X = X.fillna(X.median(numeric_only=True)).fillna(0)

    y = (df["dir_24h"] > 0).astype(int)

    return X, y, df["ts"].values, keep
