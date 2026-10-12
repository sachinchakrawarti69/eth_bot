"""Train: fit HMM on returns, then one logistic per state."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score

from ml.dataset import build
from ml.predictors.hmm_logistic.config import (
    HMM_PARAMS, LOGISTIC_PARAMS, FEATURES, TARGET, MODEL_NAME,
)


ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "database" / "market.db"
MODELS_DIR = ROOT / "ml" / "_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


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
    # ---- 1. fit HMM on daily returns
    rets_df = load_returns(symbol)
    rets = rets_df["ret"].values.reshape(-1, 1)

    hmm = GaussianHMM(**HMM_PARAMS)
    hmm.fit(rets)
    states = hmm.predict(rets)

    # label states by mean return
    means = {}
    for s in range(HMM_PARAMS["n_components"]):
        mask = states == s
        means[s] = float(rets[mask].mean()) if mask.any() else 0.0
    order = sorted(means, key=lambda k: means[k])
    labels = {order[0]: "bear", order[1]: "chop", order[2]: "bull"}

    # ---- 2. build feature matrix with state column
    X, y, ts, _ = build(symbol, FEATURES, TARGET)

    # align states to feature rows
    dates = pd.to_datetime(ts, unit="ms", utc=True).tz_convert(None)
    rets_df["state"] = states
    state_by_date = rets_df["state"].reindex(dates, method="ffill").fillna(-1).astype(int).values

    # ---- 3. split chronologically
    n = len(X)
    split = int(n * (1 - holdout))
    X_tr, X_te = X.iloc[:split].copy(), X.iloc[split:].copy()
    y_tr, y_te = y.iloc[:split], y.iloc[split:]
    s_tr, s_te = state_by_date[:split], state_by_date[split:]

    # ---- 4. train one LR per state
    models = {}
    for raw_state in range(HMM_PARAMS["n_components"]):
        mask = s_tr == raw_state
        if mask.sum() < 20:
            continue
        m = LogisticRegression(**LOGISTIC_PARAMS)
        m.fit(X_tr[mask], y_tr[mask])
        models[raw_state] = m

    # ---- 5. evaluate on holdout
    probs = np.full(len(X_te), 0.5)
    for i, (idx, row) in enumerate(X_te.iterrows()):
        raw = s_te[i]
        m = models.get(raw)
        if m is not None:
            probs[i] = m.predict_proba(row.values.reshape(1, -1))[0, 1]

    pred = (probs > 0.5).astype(int)

    metrics = {
        "symbol":      symbol,
        "model":       MODEL_NAME,
        "n_train":     int(len(X_tr)),
        "n_test":      int(len(X_te)),
        "n_states_fit": len(models),
        "accuracy":    float(accuracy_score(y_te, pred)),
        "auc":         float(roc_auc_score(y_te, probs)),
        "labels":      {int(k): v for k, v in labels.items()},
        "features":    FEATURES,
        "target":      TARGET,
    }

    path = MODELS_DIR / (symbol + "_" + MODEL_NAME + ".joblib")
    joblib.dump({
        "hmm":       hmm,
        "logistics": models,
        "labels":    labels,
        "features":  FEATURES,
        "target":    TARGET,
    }, path)

    return metrics, path
