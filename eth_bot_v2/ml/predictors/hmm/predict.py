"""Predict current regime with the HMM."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "database" / "market.db"
MODELS_DIR = ROOT / "ml" / "_models"


def load(symbol):
    path = MODELS_DIR / (symbol + "_hmm.joblib")
    if not path.exists():
        raise RuntimeError("no model at " + str(path))
    return joblib.load(path)


def current_state(symbol):
    bundle = load(symbol)
    model = bundle["model"]
    labels = bundle["labels"]

    with sqlite3.connect(DB) as c:
        df = pd.read_sql_query(
            "SELECT open_time, close FROM ohlcv "
            "WHERE symbol=? AND timeframe='1d' ORDER BY open_time DESC LIMIT 90",
            c, params=(symbol,))
    df = df.sort_values("open_time")
    df["ret"] = df["close"].pct_change()
    df = df.dropna()

    states = model.predict(df["ret"].values.reshape(-1, 1))
    state = int(states[-1])

    # count consecutive days in this state
    days = 0
    for s in reversed(states):
        if int(s) == state:
            days += 1
        else:
            break

    return {
        "symbol":     symbol,
        "raw_state":  state,
        "state":      labels.get(state, "unknown"),
        "state_days": days,
    }


def predict(symbol, row=None):
    info = current_state(symbol)
    return {
        "symbol":     symbol,
        "prob_up":    None,
        "prob_down":  None,
        "direction":  info["state"],
        "confidence": None,
        "extra":      info,
    }
