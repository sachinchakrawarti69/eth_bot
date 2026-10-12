"""Build X (features) and y (labels) from the features table."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"


# default feature set used when caller does not pass one
DEFAULT_FEATURES = [
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

DEFAULT_TARGET = "dir_24h"


def load(symbol: str = "ETHUSDT") -> pd.DataFrame:
    """Load raw features table for a symbol."""
    with sqlite3.connect(DB_PATH) as c:
        df = pd.read_sql_query(
            "SELECT * FROM features WHERE symbol=? ORDER BY ts",
            c, params=(symbol,))
    return df


def build(symbol: str = "ETHUSDT",
          features=None,
          target: str = DEFAULT_TARGET):
    """
    Return (X, y, ts, used_features).

    X : DataFrame of features (numeric, NaN-filled)
    y : Series of binary labels (0/1)
    ts: numpy array of timestamps in ms
    used_features: list of feature names actually present
    """
    df = load(symbol)
    if df.empty:
        raise RuntimeError("no features for " + symbol)

    # drop rows without a target
    if target not in df.columns:
        raise KeyError("target column missing: " + target)
    df = df[df[target].notna()].copy()

    # regime is a string -- encode it
    if "regime" in df.columns:
        regime_map = {"bull": 2, "chop": 1, "bear": 0}
        df["regime_enc"] = df["regime"].map(regime_map).fillna(1).astype(int)

    # resolve feature list
    if features is None:
        features = list(DEFAULT_FEATURES)
        if "regime" in df.columns:
            features = features + ["regime_enc"]

    # keep only features that exist in the table
    present = [f for f in features if f in df.columns]
    missing = [f for f in features if f not in df.columns]
    if missing:
        # silently drop missing -- many come from sparse futures data
        pass

    if not present:
        raise RuntimeError("no features available in features table")

    # keep only rows with at least 50% coverage on `present`
    cov = df[present].notna().mean(axis=1)
    df = df[cov >= 0.5].copy()

    X = df[present].copy()
    X = X.fillna(X.median(numeric_only=True)).fillna(0)

    # target
    y = df[target]
    # convert to int if it is bool-like
    y = y.astype(int)

    ts = df["ts"].values
    return X, y, ts, present


if __name__ == "__main__":
    X, y, ts, feats = build("ETHUSDT")
    print("X shape :", X.shape)
    print("y shape :", y.shape)
    print("classes :", y.value_counts().to_dict())
    print("features:", feats)
