"""Show which features moved the state-conditional prediction."""

from __future__ import annotations
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / "ml" / "_models"


def explain(symbol: str, row: pd.Series, top_n: int = 8) -> pd.DataFrame:
    from ml.predictors.hmm_logistic.predict import current_state

    path = MODELS_DIR / (symbol + "_hmm_logistic.joblib")
    bundle = joblib.load(path)
    features = bundle["features"]
    models = bundle["logistics"]
    labels = bundle["labels"]

    raw_state = current_state(symbol, bundle)
    m = models.get(raw_state)
    if m is None:
        return pd.DataFrame()

    x = np.array([row[features].values], dtype=float)
    x = np.nan_to_num(x, nan=0.0)

    contrib = m.coef_[0] * x[0]
    df = pd.DataFrame({
        "feature":      features,
        "value":        x[0],
        "coefficient":  m.coef_[0],
        "contribution": contrib,
        "state":        labels.get(raw_state, "unknown"),
    })
    df["abs_contrib"] = df["contribution"].abs()
    return df.sort_values("abs_contrib", ascending=False).head(top_n)
