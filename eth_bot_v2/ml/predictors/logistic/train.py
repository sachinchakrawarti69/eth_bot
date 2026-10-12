"""Train the logistic predictor."""

from __future__ import annotations
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score

from ml.dataset import build
from ml.predictors.logistic.config import (
    HYPERPARAMS, FEATURES, TARGET, MODEL_NAME,
)


ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / "ml" / "_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train(symbol: str, holdout: float = 0.2):
    X, y, ts, _ = build(symbol, FEATURES, TARGET)

    n = len(X)
    split = int(n * (1 - holdout))
    X_tr, X_te = X.iloc[:split], X.iloc[split:]
    y_tr, y_te = y.iloc[:split], y.iloc[split:]

    model = LogisticRegression(**HYPERPARAMS)
    model.fit(X_tr, y_tr)

    p_te = model.predict_proba(X_te)[:, 1]
    pred = (p_te > 0.5).astype(int)

    metrics = {
        "symbol":      symbol,
        "model":       MODEL_NAME,
        "n_train":     int(len(X_tr)),
        "n_test":      int(len(X_te)),
        "accuracy":    float(accuracy_score(y_te, pred)),
        "auc":         float(roc_auc_score(y_te, p_te)),
        "features":    FEATURES,
        "target":      TARGET,
        "hyperparams": HYPERPARAMS,
    }

    path = MODELS_DIR / (symbol + "_" + MODEL_NAME + ".joblib")
    joblib.dump({
        "model":    model,
        "features": FEATURES,
        "target":   TARGET,
    }, path)

    return metrics, path
