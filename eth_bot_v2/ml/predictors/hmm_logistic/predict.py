"""Predict with HMM + per-state logistic."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "database" / "market.db"
MODELS_DIR = ROOT / "ml" / "_models"


def load(symbol: str):
    path = MODELS_DIR / (symbol + "_hmm_logistic.joblib")
    if not path.exists():
        raise RuntimeError("no model at " + str(path))
    return joblib.load(path)


def current_state(symbol: str, bundle):
    hmm = bundle["hmm"]
    with sqlite3.connect(DB) as c:
        df = pd.read_sql_query(
            "SELECT open_time, close FROM ohlcv "
            "WHERE symbol=? AND timeframe='1d' ORDER BY open_time DESC LIMIT 60",
            c, params=(symbol,))
    df = df.sort_values("open_time")
    df["ret"] = df["close"].pct_change()
    df = df.dropna()
    states = hmm.predict(df["ret"].values.reshape(-1, 1))
    return int(states[-1])


def predict(symbol: str, row: pd.Series) -> dict:
    bundle = load(symbol)
    labels = bundle["labels"]
    features = bundle["features"]
    models = bundle["logistics"]

    raw_state = current_state(symbol, bundle)
    state_name = labels.get(raw_state, "unknown")

    m = models.get(raw_state)
    if m is None:
        p_up = 0.5
    else:
        x = pd.DataFrame([row[features].values], columns=features).fillna(0)
        p_up = float(m.predict_proba(x)[0, 1])

    return {
        "symbol":     symbol,
        "state":      state_name,
        "raw_state":  raw_state,
        "prob_up":    p_up,
        "prob_down":  1 - p_up,
        "direction":  "UP" if p_up > 0.5 else "DOWN",
        "confidence": abs(p_up - 0.5) * 2,
    }
