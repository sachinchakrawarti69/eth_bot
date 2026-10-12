"""Train a classifier to predict next-24h direction."""

from __future__ import annotations
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score,
    classification_report,
)
from sklearn.model_selection import TimeSeriesSplit

from ml.dataset import build


ROOT       = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "ml" / "_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def walk_forward_auc(X, y, n_splits=5):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    aucs, accs = [], []
    for tr, te in tscv.split(X):
        m = GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.05,
            max_depth=3, random_state=42)
        m.fit(X.iloc[tr], y.iloc[tr])
        p = m.predict_proba(X.iloc[te])[:, 1]
        try:
            aucs.append(roc_auc_score(y.iloc[te], p))
            accs.append(accuracy_score(y.iloc[te], (p > 0.5).astype(int)))
        except Exception:
            pass
    return float(np.mean(aucs) if aucs else 0), float(np.mean(accs) if accs else 0)


def train(symbol, holdout_frac=0.2):
    print("[" + symbol + "] loading features...")
    X, y, ts, keep = build(symbol)
    print("  X shape      : " + str(X.shape))
    print("  features kept: " + str(len(keep)))
    print("  classes      : " + str(y.value_counts().to_dict()))

    n = len(X)
    split = int(n * (1 - holdout_frac))
    X_tr, X_te = X.iloc[:split], X.iloc[split:]
    y_tr, y_te = y.iloc[:split], y.iloc[split:]
    print("  train rows   : " + str(len(X_tr)))
    print("  test rows    : " + str(len(X_te)))

    print("  training...")
    model = GradientBoostingClassifier(
        n_estimators=300, learning_rate=0.05,
        max_depth=4, subsample=0.9, random_state=42)
    model.fit(X_tr, y_tr)

    p_te = model.predict_proba(X_te)[:, 1]
    pred = (p_te > 0.5).astype(int)
    acc  = accuracy_score(y_te, pred)
    try:
        auc = roc_auc_score(y_te, p_te)
    except Exception:
        auc = float("nan")
    prec = precision_score(y_te, pred, zero_division=0)
    rec  = recall_score(y_te, pred, zero_division=0)

    print()
    print("  holdout accuracy : " + format(acc, ".4f"))
    print("  holdout AUC      : " + format(auc, ".4f"))
    print("  precision        : " + format(prec, ".4f"))
    print("  recall           : " + format(rec, ".4f"))
    print()
    print(classification_report(y_te, pred, digits=3))

    print("  walk-forward validation...")
    wf_auc, wf_acc = walk_forward_auc(X, y, n_splits=5)
    print("  WF AUC           : " + format(wf_auc, ".4f"))
    print("  WF accuracy      : " + format(wf_acc, ".4f"))

    imp = pd.Series(model.feature_importances_, index=X.columns)
    imp = imp.sort_values(ascending=False)
    print()
    print("  top 10 features:")
    for name, val in imp.head(10).items():
        print("    " + format(name, "<20") + " " + format(val, ".4f"))

    model_path = MODELS_DIR / (symbol + ".joblib")
    meta_path  = MODELS_DIR / (symbol + ".json")

    joblib.dump({"model": model, "features": list(X.columns)}, model_path)

    meta = {
        "symbol": symbol,
        "trained_at": pd.Timestamp.utcnow().isoformat(),
        "n_train": int(len(X_tr)),
        "n_test": int(len(X_te)),
        "accuracy": float(acc),
        "auc": float(auc),
        "wf_auc": float(wf_auc),
        "wf_accuracy": float(wf_acc),
        "top_features": {str(k): float(v) for k, v in imp.head(20).items()},
        "features": list(X.columns),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print()
    print("  saved model : " + str(model_path))
    print("  saved meta  : " + str(meta_path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="ETHUSDT")
    args = ap.parse_args()

    print("=" * 60)
    print("  TRAIN MODEL")
    print("=" * 60)
    print("  symbol: " + args.symbol)
    print()

    train(args.symbol)


if __name__ == "__main__":
    main()
