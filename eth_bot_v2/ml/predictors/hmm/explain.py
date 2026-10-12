"""Show regime history."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "database" / "market.db"
MODELS_DIR = ROOT / "ml" / "_models"


def explain(symbol: str, days: int = 30) -> pd.DataFrame:
    path = MODELS_DIR / (symbol + "_hmm.joblib")
    bundle = joblib.load(path)
    model = bundle["model"]
    labels = bundle["labels"]

    with sqlite3.connect(DB) as c:
        df = pd.read_sql_query(
            "SELECT open_time, close FROM ohlcv "
            "WHERE symbol=? AND timeframe='1d' ORDER BY open_time DESC LIMIT ?",
            c, params=(symbol, days))
    df = df.sort_values("open_time")
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df["ret"] = df["close"].pct_change()
    df = df.dropna()

    states = model.predict(df["ret"].values.reshape(-1, 1))
    df["state"] = [labels.get(int(s), "?") for s in states]
    return df[["date", "close", "ret", "state"]]
