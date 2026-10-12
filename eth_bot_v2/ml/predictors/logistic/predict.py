"""Predict with the logistic predictor."""

from __future__ import annotations
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / "ml" / "_models"


def load(symbol: str):
    path = MODELS_DIR / (symbol + "_logistic.joblib")
    if not path.exists():
        raise RuntimeError("no model at " + str(path))
    return joblib.load(path)


def predict(symbol: str, row: pd.Series) -> dict:
    bundle = load(symbol)
    model = bundle["model"]
    features = bundle["features"]

    x = pd.DataFrame([row[features].values], columns=features).fillna(0)
    p_up = float(model.predict_proba(x)[0, 1])

    return {
        "symbol":     symbol,
        "prob_up":    p_up,
        "prob_down":  1 - p_up,
        "direction":  "UP" if p_up > 0.5 else "DOWN",
        "confidence": abs(p_up - 0.5) * 2,
    }
