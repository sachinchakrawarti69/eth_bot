"""Train any predictor via the registry.

Usage:
    python -m ml.train --symbol ETHUSDT --model logistic
    python -m ml.train --symbol ETHUSDT --model hmm
    python -m ml.train --symbol ETHUSDT --model hmm_logistic
    python -m ml.train --symbol ETHUSDT --model naive_bayes
    python -m ml.train --symbol ETHUSDT --model all
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from ml.predictors import registry


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "ml" / "_runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def run_one(symbol, model_name):
    print()
    print("-" * 60)
    print("  [" + symbol + "] " + model_name)
    print("-" * 60)

    mod = registry.get(model_name)
    metrics, path = mod.train(symbol)

    # save run log
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    run_dir = RUNS_DIR / (stamp + "_" + symbol + "_" + model_name)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str), encoding="utf-8")

    # print
    for k, v in metrics.items():
        if k in ("features", "hyperparams", "labels", "state_means"):
            continue
        print("  " + format(k, "<14") + ": " + str(v))

    print("  saved         : " + str(path.relative_to(ROOT)))
    print("  run log       : " + str(run_dir.relative_to(ROOT)))

    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="ETHUSDT")
    ap.add_argument("--model",  default="logistic")
    args = ap.parse_args()

    if args.model == "all":
        models = registry.list_all()
    else:
        models = [args.model]

    print("=" * 60)
    print("  TRAIN")
    print("=" * 60)
    print("  symbol : " + args.symbol)
    print("  models : " + ", ".join(models))

    results = {}
    for m in models:
        try:
            results[m] = run_one(args.symbol, m)
        except Exception as e:
            print()
            print("  FAILED " + m + ": " + type(e).__name__ + ": " + str(e))
            import traceback
            traceback.print_exc()

    # summary
    if results:
        print()
        print("=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print("  " + format("model", "<16") +
              format("accuracy", ">10") +
              format("auc", ">10"))
        print("  " + "-" * 40)
        for m, r in results.items():
            acc = r.get("accuracy", 0)
            auc = r.get("auc", 0)
            print("  " + format(m, "<16") +
                  format(acc, ">10.4f") +
                  format(auc, ">10.4f"))


if __name__ == "__main__":
    main()
