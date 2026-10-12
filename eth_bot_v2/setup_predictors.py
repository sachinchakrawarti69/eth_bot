"""
setup_predictors.py

Creates ml/predictors/ with:
    registry.py
    logistic/       (5 files)
    hmm/            (5 files)
    hmm_logistic/   (5 files)
    naive_bayes/    (5 files)

Run:
    python setup_predictors.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRED = ROOT / "ml" / "predictors"


# ================================================================
#  registry.py
# ================================================================

REGISTRY = '''"""Model registry -- name -> module mapping."""

from __future__ import annotations
from importlib import import_module

_REGISTRY = {}


def register(name, module_path):
    """Register a predictor module by name."""
    _REGISTRY[name] = module_path


def get(name):
    """Return the module for a predictor."""
    if name not in _REGISTRY:
        raise KeyError("unknown predictor: " + name +
                       ". known: " + str(list(_REGISTRY)))
    return import_module(_REGISTRY[name])


def list_all():
    return list(_REGISTRY)


# -------- register predictors here --------
register("logistic",     "ml.predictors.logistic")
register("hmm",          "ml.predictors.hmm")
register("hmm_logistic", "ml.predictors.hmm_logistic")
register("naive_bayes",  "ml.predictors.naive_bayes")
'''


# ================================================================
#  logistic
# ================================================================

LOGISTIC_CONFIG = '''"""Hyperparameters for the logistic predictor."""

MODEL_NAME = "logistic"

HYPERPARAMS = {
    "C": 1.0,
    "max_iter": 1000,
    "class_weight": None,
    "solver": "lbfgs",
    "random_state": 42,
}

FEATURES = [
    "rsi_14", "macd_hist", "vol_20",
    "dist_sma50", "dist_sma200",
    "funding", "hour",
]

TARGET = "dir_24h"
'''

LOGISTIC_TRAIN = '''"""Train the logistic predictor."""

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
'''

LOGISTIC_PREDICT = '''"""Predict with the logistic predictor."""

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
'''

LOGISTIC_EXPLAIN = '''"""Explain a logistic prediction with per-feature contributions."""

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
'''


# ================================================================
#  hmm
# ================================================================

HMM_CONFIG = '''"""Hyperparameters for the HMM predictor."""

MODEL_NAME = "hmm"

HYPERPARAMS = {
    "n_components": 3,
    "covariance_type": "diag",
    "n_iter": 100,
    "random_state": 42,
}

FEATURES = ["close"]         # HMM uses returns only
TARGET   = "dir_24h"         # not used during fit, only for evaluation
'''

HMM_TRAIN = '''"""Train the HMM predictor on daily returns."""

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
'''

HMM_PREDICT = '''"""Predict current regime with the HMM."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "database" / "market.db"
MODELS_DIR = ROOT / "ml" / "_models"


def load(symbol: str):
    path = MODELS_DIR / (symbol + "_hmm.joblib")
    if not path.exists():
        raise RuntimeError("no model at " + str(path))
    return joblib.load(path)


def current_state(symbol: str):
    """Return today's hidden state."""
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

    return {
        "symbol":     symbol,
        "raw_state":  state,
        "state":      labels.get(state, "unknown"),
        "state_days": int((states == state)[::-1].argmin()),
    }


def predict(symbol: str, row: pd.Series = None) -> dict:
    info = current_state(symbol)
    return {
        "symbol":     symbol,
        "prob_up":    None,          # HMM alone does not give probability
        "prob_down":  None,
        "direction":  info["state"],
        "confidence": None,
        "extra":      info,
    }
'''

HMM_EXPLAIN = '''"""Show regime history."""

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
'''


# ================================================================
#  hmm_logistic
# ================================================================

HMM_LOG_CONFIG = '''"""Hyperparameters for the HMM + state-conditional logistic predictor."""

MODEL_NAME = "hmm_logistic"

HMM_PARAMS = {
    "n_components": 3,
    "covariance_type": "diag",
    "n_iter": 100,
    "random_state": 42,
}

LOGISTIC_PARAMS = {
    "C": 1.0,
    "max_iter": 1000,
    "random_state": 42,
}

FEATURES = [
    "rsi_14", "macd_hist", "vol_20",
    "dist_sma50", "dist_sma200",
    "funding", "hour",
]

TARGET = "dir_24h"
'''

HMM_LOG_TRAIN = '''"""Train: fit HMM on returns, then one logistic per state."""

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
'''

HMM_LOG_PREDICT = '''"""Predict with HMM + per-state logistic."""

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
'''

HMM_LOG_EXPLAIN = '''"""Show which features moved the state-conditional prediction."""

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
'''


# ================================================================
#  naive_bayes
# ================================================================

NB_CONFIG = '''"""Hyperparameters for the Gaussian Naive Bayes predictor."""

MODEL_NAME = "naive_bayes"

HYPERPARAMS = {
    "var_smoothing": 1e-9,
}

FEATURES = [
    "rsi_14", "macd_hist", "vol_20",
    "dist_sma50", "funding", "hour",
]

TARGET = "dir_24h"
'''

NB_TRAIN = '''"""Train the Gaussian Naive Bayes predictor."""

from __future__ import annotations
from pathlib import Path

import joblib
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, roc_auc_score

from ml.dataset import build
from ml.predictors.naive_bayes.config import (
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

    model = GaussianNB(**HYPERPARAMS)
    model.fit(X_tr, y_tr)

    p_te = model.predict_proba(X_te)[:, 1]
    pred = (p_te > 0.5).astype(int)

    metrics = {
        "symbol":   symbol,
        "model":    MODEL_NAME,
        "n_train":  int(len(X_tr)),
        "n_test":   int(len(X_te)),
        "accuracy": float(accuracy_score(y_te, pred)),
        "auc":      float(roc_auc_score(y_te, p_te)),
        "features": FEATURES,
        "target":   TARGET,
        "hyperparams": HYPERPARAMS,
    }

    path = MODELS_DIR / (symbol + "_" + MODEL_NAME + ".joblib")
    joblib.dump({
        "model":    model,
        "features": FEATURES,
        "target":   TARGET,
    }, path)

    return metrics, path
'''

NB_PREDICT = '''"""Predict with Naive Bayes."""

from __future__ import annotations
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / "ml" / "_models"


def load(symbol: str):
    path = MODELS_DIR / (symbol + "_naive_bayes.joblib")
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
'''

NB_EXPLAIN = '''"""Explain a Naive Bayes prediction."""

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
'''


# ================================================================
#  WRITE EVERYTHING
# ================================================================

FILES = {

    # registry
    "registry.py": REGISTRY,

    # logistic
    "logistic/__init__.py":     "",
    "logistic/config.py":       LOGISTIC_CONFIG,
    "logistic/train.py":        LOGISTIC_TRAIN,
    "logistic/predict.py":      LOGISTIC_PREDICT,
    "logistic/explain.py":      LOGISTIC_EXPLAIN,

    # hmm
    "hmm/__init__.py":          "",
    "hmm/config.py":            HMM_CONFIG,
    "hmm/train.py":             HMM_TRAIN,
    "hmm/predict.py":           HMM_PREDICT,
    "hmm/explain.py":           HMM_EXPLAIN,

    # hmm + logistic
    "hmm_logistic/__init__.py": "",
    "hmm_logistic/config.py":   HMM_LOG_CONFIG,
    "hmm_logistic/train.py":    HMM_LOG_TRAIN,
    "hmm_logistic/predict.py":  HMM_LOG_PREDICT,
    "hmm_logistic/explain.py":  HMM_LOG_EXPLAIN,

    # naive_bayes
    "naive_bayes/__init__.py":  "",
    "naive_bayes/config.py":    NB_CONFIG,
    "naive_bayes/train.py":     NB_TRAIN,
    "naive_bayes/predict.py":   NB_PREDICT,
    "naive_bayes/explain.py":   NB_EXPLAIN,
}


def main():
    print("=" * 60)
    print("  SETUP ml/predictors/")
    print("=" * 60)
    print()

    PRED.mkdir(parents=True, exist_ok=True)

    for rel, content in FILES.items():
        p = PRED / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print("  wrote " + str(p.relative_to(ROOT)) +
              "  (" + str(content.count(chr(10)) + 1) + " lines)")

    # syntax check
    print()
    print("  verifying syntax...")
    import ast
    ok = 0
    for rel in FILES:
        if rel.endswith("__init__.py"):
            continue
        p = PRED / rel
        try:
            ast.parse(p.read_text(encoding="utf-8"))
            print("  OK " + rel)
            ok += 1
        except SyntaxError as e:
            print("  FAIL " + rel + " : " + str(e))

    print()
    print("  " + str(ok) + " files OK")
    print()
    print("=" * 60)
    print("  DONE")
    print("=" * 60)
    print()
    print("  Next:")
    print("    python -m ml.train --symbol ETHUSDT --model logistic")
    print("    python -m ml.train --symbol ETHUSDT --model hmm")
    print("    python -m ml.train --symbol ETHUSDT --model hmm_logistic")
    print("    python -m ml.train --symbol ETHUSDT --model naive_bayes")
    print()


if __name__ == "__main__":
    main()