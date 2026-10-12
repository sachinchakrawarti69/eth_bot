"""CLI: get today's ML-based trade plan for one or more symbols.

Usage:
    python -m scripts_python.signals.ml_plan
    python -m scripts_python.signals.ml_plan --symbols BTCUSDT,ETHUSDT
    python -m scripts_python.signals.ml_plan --account 5000 --risk 0.5
"""

from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ml.plan import build_plan, print_plan


ROOT    = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "ml_plans"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    ap.add_argument("--account", type=float, default=1000.0)
    ap.add_argument("--risk", type=float, default=1.0)
    ap.add_argument("--min-conf", type=float, default=0.30)
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    print("=" * 66)
    print("  ML TRADE PLANS")
    print("=" * 66)
    print("  time    : " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("  symbols : " + ", ".join(symbols))
    print("  account : $" + format(args.account, ",.2f") + "   risk " + str(args.risk) + "%")
    print("  min conf: " + str(args.min_conf))

    plans = []
    for sym in symbols:
        try:
            p = build_plan(sym, args.account, args.risk, args.min_conf)
            print_plan(p)
            if p:
                plans.append(p)
        except Exception as e:
            print("\n  [" + sym + "] error: " + type(e).__name__ + ": " + str(e))

    if plans:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        path  = OUT_DIR / (stamp + ".json")
        path.write_text(json.dumps(plans, indent=2, default=str), encoding="utf-8")
        print("\n  saved " + str(path))


if __name__ == "__main__":
    main()
