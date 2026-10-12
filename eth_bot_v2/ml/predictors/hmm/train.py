"""Train the HMM predictor on daily returns."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM


ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "database" / "market.db"
MODELS_DIR = ROOT / "ml" / "_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

from ml.predictors.hmm.config import HYPERPARAMS, MODEL_NAME


def load_returns(symbol: str):
    with sqlite3.connect(DB) as c:
        df = pd.read_sql_query(
            "SELECT open_time, close FROM ohlcv "
            "WHERE symbol=? AND timeframe='1d' ORDER BY open_time",
            c, params=(symbol,))
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.set_index("date")
    df["ret"] = df["close"].pct_change()
    return df.dropna()


def train(symbol: str, holdout: float = 0.2):
    df = load_returns(symbol)
    rets = df["ret"].values.reshape(-1, 1)

    model = GaussianHMM(**HYPERPARAMS)
    model.fit(rets)

    states = model.predict(rets)

    # label each state by mean return
    means = {}
    for s in range(HYPERPARAMS["n_components"]):
        mask = states == s
        means[s] = float(rets[mask].mean()) if mask.any() else 0.0

    # map raw state -> semantic name
    order = sorted(means, key=lambda k: means[k])
    labels = {order[0]: "bear", order[1]: "chop", order[2]: "bull"}

    metrics = {
        "symbol":       symbol,
        "model":        MODEL_NAME,
        "n_states":     HYPERPARAMS["n_components"],
        "state_means":  means,
        "labels":       {int(k): v for k, v in labels.items()},
        "n_samples":    int(len(df)),
    }

    path = MODELS_DIR / (symbol + "_" + MODEL_NAME + ".joblib")
    joblib.dump({"model": model, "labels": labels}, path)

    return metrics, path
