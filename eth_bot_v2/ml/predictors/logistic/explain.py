"""Explain a logistic prediction with per-feature contributions."""

from __future__ import annotations
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / "ml" / "_models"


def explain(symbol: str, row: pd.Series, top_n: int = 8) -> pd.DataFrame:
    path = MODELS_DIR / (symbol + "_logistic.joblib")
    bundle = joblib.load(path)
    model = bundle["model"]
    features = bundle["features"]

    x = np.array([row[features].values], dtype=float)
    x = np.nan_to_num(x, nan=0.0)

    contrib = model.coef_[0] * x[0]
    df = pd.DataFrame({
        "feature":      features,
        "value":        x[0],
        "coefficient":  model.coef_[0],
        "contribution": contrib,
    })
    df["abs_contrib"] = df["contribution"].abs()
    return df.sort_values("abs_contrib", ascending=False).head(top_n)
