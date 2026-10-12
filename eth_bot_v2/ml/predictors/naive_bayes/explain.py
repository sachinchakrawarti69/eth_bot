"""Explain a Naive Bayes prediction."""

from __future__ import annotations
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / "ml" / "_models"


def explain(symbol: str, row: pd.Series, top_n: int = 8) -> pd.DataFrame:
    path = MODELS_DIR / (symbol + "_naive_bayes.joblib")
    bundle = joblib.load(path)
    model = bundle["model"]
    features = bundle["features"]

    x = np.array([row[features].values], dtype=float)
    x = np.nan_to_num(x, nan=0.0)

    # log-likelihood ratio per feature
    theta_up   = model.theta_[1]
    theta_down = model.theta_[0]
    var        = model.var_
    lr = ((theta_up - theta_down) / var) * (x[0] - (theta_up + theta_down) / 2)

    df = pd.DataFrame({
        "feature":      features,
        "value":        x[0],
        "log_lik_ratio": lr,
    })
    df["abs_contrib"] = df["log_lik_ratio"].abs()
    return df.sort_values("abs_contrib", ascending=False).head(top_n)
