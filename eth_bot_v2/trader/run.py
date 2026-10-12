"""CLI: check today's signals.

Usage:
    python -m trader.run
    python -m trader.run --symbols BTCUSDT,ETHUSDT
    python -m trader.run --account 5000 --risk 2.0
"""

from __future__ import annotations
import argparse

from trader.plan import build, print_plan, save


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    ap.add_argument("--account", type=float, default=1000.0)
    ap.add_argument("--risk", type=float, default=2.0)
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    print("=" * 66)
    print("  DAILY TRADE SIGNAL")
    print("=" * 66)
    print("  strategy: trend_follow")
    print("  rule    : buy bull regime + MACD>0, hold 30 days")
    print("  account : $" + format(args.account, ",.2f"))
    print("  risk    : " + str(args.risk) + "% per trade")

    for sym in symbols:
        try:
            p = build(sym, args.account, args.risk)
            print_plan(p)
            path = save(p)
            if path:
                print("  saved: " + str(path))
        except Exception as e:
            print()
            print("  [" + sym + "] error: " + type(e).__name__ + ": " + str(e))


if __name__ == "__main__":
    main()
