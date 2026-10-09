"""Run the 6-year backtest.

Usage:
    python -m bt6.run
    python -m bt6.run --symbol ETHUSDT
    python -m bt6.run --symbol BTCUSDT
"""

from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from bt6.data       import load_daily
from bt6.strategies import STRATEGIES
from bt6.engine     import simulate, metrics, verdict


ROOT    = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "backtest6y"


def run_one(symbol, name, strategy, df):
    trades = simulate(df, strategy)
    m = metrics(trades)
    if m is None:
        return None

    print()
    print("=" * 70)
    print("  " + name + "  --  " + symbol)
    print("  " + strategy["desc"])
    print("=" * 70)
    print("  trades       : " + str(m["n"]))
    print("  hit rate     : " + format(m["hit_rate"] * 100, ".1f") + "%")
    print("  avg win      : " + format(m["avg_win"] * 100, "+.3f") + "%")
    print("  avg loss     : " + format(m["avg_loss"] * 100, "+.3f") + "%")
    print("  expectancy   : " + format(m["expectancy"] * 100, "+.3f") + "%")
    print("  total return : " + format(m["total_return"] * 100, "+.1f") + "%")
    print("  max DD       : " + format(m["max_dd"] * 100, ".1f") + "%")
    print("  sharpe       : " + format(m["sharpe"], ".2f"))
    print("  profit factor: " + format(m["profit_factor"], ".2f"))
    print("  years +      : " + str(m["pos_years"]) + "/" + str(m["total_years"]))
    print("  verdict      : " + verdict(m))
    print()
    print("  per year:")
    for y in m["by_year"]:
        print("    " + str(y["year"]) + "  N=" + str(y["n"]).rjust(3) +
              "  hit=" + format(y["hit"] * 100, ".0f") + "%" +
              "  ret=" + format(y["total_return"] * 100, "+.1f") + "%")

    return {
        "strategy":     name,
        "symbol":       symbol,
        "desc":         strategy["desc"],
        "n":            m["n"],
        "hit_rate":     m["hit_rate"],
        "avg_win":      m["avg_win"],
        "avg_loss":     m["avg_loss"],
        "expectancy":   m["expectancy"],
        "total_return": m["total_return"],
        "max_dd":       m["max_dd"],
        "sharpe":       m["sharpe"],
        "profit_factor":m["profit_factor"],
        "pos_years":    m["pos_years"],
        "total_years":  m["total_years"],
        "verdict":      verdict(m),
        "by_year":      m["by_year"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="ETHUSDT")
    ap.add_argument("--symbols", default=None)
    args = ap.parse_args()

    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = [args.symbol]

    print("=" * 70)
    print("  6-YEAR BACKTEST")
    print("=" * 70)
    print("  symbols  : " + ", ".join(symbols))
    print("  fee/trip : 0.10%")
    print("  strategies: " + str(len(STRATEGIES)))

    all_results = []

    for symbol in symbols:
        df = load_daily(symbol)
        print()
        print("[" + symbol + "]  " + str(len(df)) + " daily bars  "
              + str(df.index.min().date()) + " -> " + str(df.index.max().date()))

        for name, s in STRATEGIES.items():
            r = run_one(symbol, name, s, df)
            if r:
                all_results.append(r)

    # save
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    path  = OUT_DIR / (stamp + ".json")
    path.write_text(json.dumps(all_results, indent=2, default=str), encoding="utf-8")

    # summary
    print()
    print("=" * 70)
    print("  SUMMARY  (sorted by total return)")
    print("=" * 70)
    print("  " + format("strategy", "<22") +
          format("symbol", "<10") +
          format("N", ">5") +
          format("hit%", ">7") +
          format("exp%", ">8") +
          format("ret%", ">10") +
          format("sharpe", ">8") +
          format("verdict", ">10"))
    print("  " + "-" * 80)

    all_results.sort(key=lambda r: -r["total_return"])
    for r in all_results:
        print("  " + format(r["strategy"], "<22") +
              format(r["symbol"], "<10") +
              format(str(r["n"]), ">5") +
              format(format(r["hit_rate"] * 100, ".1f"), ">7") +
              format(format(r["expectancy"] * 100, "+.3f"), ">8") +
              format(format(r["total_return"] * 100, "+.1f"), ">10") +
              format(format(r["sharpe"], ".2f"), ">8") +
              format(r["verdict"], ">10"))

    print()
    print("  saved " + str(path))


if __name__ == "__main__":
    main()
