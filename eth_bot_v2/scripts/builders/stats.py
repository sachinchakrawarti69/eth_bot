"""Statistical mode - test every signal against history.

For each signal, compute hit rate, expectancy, Sharpe, stability
across 3 horizons (1h, 4h, 24h). Rank by fees-adjusted expectancy.

Usage:
    python -m scripts_python.builders.stats
    python -m scripts_python.builders.stats --symbols BTCUSDT
    python -m scripts_python.builders.stats --min-samples 30
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"

HORIZONS = {
    "1h":  "target_1h",
    "4h":  "target_4h",
    "24h": "target_24h",
}

ROUND_TRIP_FEE = 0.0010   # 0.10% (Binance taker, both sides)


# ------------------------------------------------------------------
# signal definitions
# ------------------------------------------------------------------
# each: (name, lambda df -> boolean Series)

SIGNALS = [
    # ---- RSI (1h) ----
    ("rsi_1h < 30",              lambda d: d["rsi_14"] < 30),
    ("rsi_1h < 40",              lambda d: d["rsi_14"] < 40),
    ("rsi_1h > 60",              lambda d: d["rsi_14"] > 60),
    ("rsi_1h > 70",              lambda d: d["rsi_14"] > 70),

    # ---- RSI (4h) ----
    ("rsi_4h < 30",              lambda d: d["rsi_14_4h"] < 30),
    ("rsi_4h < 40",              lambda d: d["rsi_14_4h"] < 40),
    ("rsi_4h > 60",              lambda d: d["rsi_14_4h"] > 60),
    ("rsi_4h > 70",              lambda d: d["rsi_14_4h"] > 70),

    # ---- RSI (1d) ----
    ("rsi_1d < 30",              lambda d: d["rsi_14_1d"] < 30),
    ("rsi_1d > 70",              lambda d: d["rsi_14_1d"] > 70),

    # ---- MACD ----
    ("macd_1h > 0",              lambda d: d["macd_hist"] > 0),
    ("macd_1h < 0",              lambda d: d["macd_hist"] < 0),
    ("macd_4h > 0",              lambda d: d["macd_hist_4h"] > 0),
    ("macd_4h < 0",              lambda d: d["macd_hist_4h"] < 0),

    # ---- regime ----
    ("regime = bull",            lambda d: d["regime"] == "bull"),
    ("regime = bear",            lambda d: d["regime"] == "bear"),
    ("regime = chop",            lambda d: d["regime"] == "chop"),
    ("trend_up = 1",             lambda d: d["trend_up"] == 1),
    ("trend_down = 1",           lambda d: d["trend_down"] == 1),

    # ---- distance from MA ----
    ("dist_sma50 > 5%",          lambda d: d["dist_sma50"] > 0.05),
    ("dist_sma50 < -5%",         lambda d: d["dist_sma50"] < -0.05),
    ("dist_sma200 > 10%",        lambda d: d["dist_sma200"] > 0.10),
    ("dist_sma200 < -10%",       lambda d: d["dist_sma200"] < -0.10),

    # ---- volatility ----
    ("vol_regime = high",        lambda d: d["vol_regime"] == "high"),
    ("vol_regime = low",         lambda d: d["vol_regime"] == "low"),

    # ---- calendar ----
    ("hour = 0",                 lambda d: d["hour"] == 0),
    ("hour = 1",                 lambda d: d["hour"] == 1),
    ("hour = 2",                 lambda d: d["hour"] == 2),
    ("hour = 3",                 lambda d: d["hour"] == 3),
    ("hour = 8",                 lambda d: d["hour"] == 8),
    ("hour = 9",                 lambda d: d["hour"] == 9),
    ("hour = 13",                lambda d: d["hour"] == 13),
    ("hour = 14",                lambda d: d["hour"] == 14),
    ("hour = 15",                lambda d: d["hour"] == 15),
    ("hour = 18",                lambda d: d["hour"] == 18),
    ("hour = 20",                lambda d: d["hour"] == 20),
    ("hour = 21",                lambda d: d["hour"] == 21),
    ("hour = 22",                lambda d: d["hour"] == 22),
    ("hour in 13-15",            lambda d: d["hour"].isin([13,14,15])),
    ("hour in 18-21",            lambda d: d["hour"].isin([18,19,20,21])),
    ("hour in 0-3",              lambda d: d["hour"].isin([0,1,2,3])),
    ("weekday = Mon",            lambda d: d["weekday"] == 0),
    ("weekday = Tue",            lambda d: d["weekday"] == 1),
    ("weekday = Wed",            lambda d: d["weekday"] == 2),
    ("weekday = Thu",            lambda d: d["weekday"] == 3),
    ("weekday = Fri",            lambda d: d["weekday"] == 4),
    ("weekday = Sat",            lambda d: d["weekday"] == 5),
    ("weekday = Sun",            lambda d: d["weekday"] == 6),
    ("weekend",                  lambda d: d["weekday"].isin([5, 6])),

    # ---- funding ----
    ("funding > 0.05%",          lambda d: d["funding"] >  0.0005),
    ("funding < -0.05%",         lambda d: d["funding"] < -0.0005),
    ("funding > 0",              lambda d: d["funding"] >  0),
    ("funding < 0",              lambda d: d["funding"] <  0),

    # ---- OI ----
    ("oi_chg_24h > 5%",          lambda d: d["oi_chg_24h"] >  0.05),
    ("oi_chg_24h < -5%",         lambda d: d["oi_chg_24h"] < -0.05),

    # ---- long/short ----
    ("ls_ratio > 1.5",           lambda d: d["ls_ratio"] > 1.5),
    ("ls_ratio > 2.0",           lambda d: d["ls_ratio"] > 2.0),
    ("ls_ratio < 0.7",           lambda d: d["ls_ratio"] < 0.7),

    # ---- taker flow ----
    ("taker_ratio > 1.3",        lambda d: d["taker_ratio"] > 1.3),
    ("taker_ratio < 0.7",        lambda d: d["taker_ratio"] < 0.7),

    # ---- combined ----
    ("bull AND rsi_1h < 30",     lambda d: (d["regime"]=="bull") & (d["rsi_14"] < 30)),
    ("bear AND rsi_1h > 70",     lambda d: (d["regime"]=="bear") & (d["rsi_14"] > 70)),
    ("rsi_4h < 30 AND ls > 1.5", lambda d: (d["rsi_14_4h"] < 30) & (d["ls_ratio"] > 1.5)),
    ("hour 18-21 AND rsi < 40",  lambda d: d["hour"].isin([18,19,20,21]) & (d["rsi_14"] < 40)),
]


# ------------------------------------------------------------------
# metric computation
# ------------------------------------------------------------------

def compute_stats(returns: pd.Series, timestamps: pd.Series) -> dict | None:
    """Given a series of forward returns, compute the stats."""
    r = returns.dropna()
    n = len(r)
    if n < 10:
        return None

    wins = r[r > 0]
    losses = r[r <= 0]

    hit_rate = len(wins) / n
    avg_win  = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0    # negative

    expectancy = hit_rate * avg_win + (1 - hit_rate) * avg_loss
    net = expectancy - ROUND_TRIP_FEE

    # profit factor
    gross_win  = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")

    # Sharpe (annualized)
    if r.std(ddof=0) > 0:
        # 1h = 24*365 = 8760 bars/year; 4h = 2190; 24h = 365
        bars_per_year = {"1h": 8760, "4h": 2190, "24h": 365}
        sharpe = float(r.mean() / r.std(ddof=0))
    else:
        sharpe = 0.0

    # stability: fraction of years with positive expectancy
    years = pd.to_datetime(timestamps).dt.year
    year_expectancies = []
    for y in sorted(years.unique()):
        mask = (years == y).values
        ry = r.iloc[mask] if len(r) == len(years) else r[years == y]
        if len(ry) >= 5:
            w = ry[ry > 0]
            l = ry[ry <= 0]
            hr = len(w) / len(ry)
            aw = float(w.mean()) if len(w) else 0.0
            al = float(l.mean()) if len(l) else 0.0
            year_expectancies.append(hr * aw + (1 - hr) * al)
    stability = (
        sum(1 for x in year_expectancies if x > 0) / len(year_expectancies)
        if year_expectancies else 0.0
    )

    # max drawdown on the cumulative signal return (if always entered)
    cum = (1 + r).cumprod()
    dd = (cum / cum.cummax() - 1).min() if len(cum) else 0.0

    return {
        "n_samples":      n,
        "hit_rate":       round(hit_rate, 4),
        "avg_win":        round(avg_win, 6),
        "avg_loss":       round(avg_loss, 6),
        "expectancy":     round(expectancy, 6),
        "expectancy_net": round(net, 6),
        "sharpe":         round(sharpe, 4),
        "max_dd":         round(float(dd), 4),
        "profit_factor":  round(pf, 4) if pf != float("inf") else 999.0,
        "stability":      round(stability, 4),
    }


def verdict_for(stats: dict) -> str:
    if stats["n_samples"] < 20:
        return "none"
    net = stats["expectancy_net"]
    if net > 0.003 and stats["stability"] >= 0.6 and stats["n_samples"] >= 50:
        return "strong"
    if net > 0.001 and stats["stability"] >= 0.5:
        return "edge"
    if net > 0.0002:
        return "weak"
    if net < -0.001 and stats["stability"] <= 0.4:
        return "edge_short"
    return "none"


# ------------------------------------------------------------------
# main test loop
# ------------------------------------------------------------------

def test_all(conn, symbols, min_samples, run_ts):
    print("=" * 100)
    print("  STATISTICAL MODE")
    print("=" * 100)
    print(f"  symbols      : {', '.join(symbols)}")
    print(f"  signals      : {len(SIGNALS)}")
    print(f"  horizons     : {list(HORIZONS)}")
    print(f"  min samples  : {min_samples}")
    print(f"  fee per trip : {ROUND_TRIP_FEE*100:.2f}%")
    print()

    # load all features once
    placeholders = ",".join("?" * len(symbols))
    df = pd.read_sql_query(
        f"SELECT * FROM features WHERE symbol IN ({placeholders}) ORDER BY symbol, ts",
        conn, params=symbols)
    if df.empty:
        print("  no features found")
        return []

    print(f"  loaded {len(df):,} feature rows")
    print()

    results = []
    t0 = time.time()

    for sig_name, sig_fn in SIGNALS:
        try:
            mask = sig_fn(df)
        except Exception as e:
            print(f"  {sig_name:<30} ERROR: {e}")
            continue

        subset = df[mask]
        if len(subset) < min_samples:
            continue

        for horizon_name, col in HORIZONS.items():
            if col not in subset.columns:
                continue
            stats = compute_stats(subset[col], subset["ts"])
            if stats is None:
                continue

            verdict = verdict_for(stats)
            row = {
                "signal_name":  sig_name,
                "horizon":      horizon_name,
                "ts":           run_ts,
                "symbol":       "ALL",
                **stats,
                "verdict":      verdict,
            }
            results.append(row)

            # write to DB
            conn.execute(
                """INSERT OR REPLACE INTO signal_stats
                   (signal_name, horizon, ts, symbol, n_samples, hit_rate,
                    avg_win, avg_loss, expectancy, expectancy_net,
                    sharpe, max_dd, profit_factor, stability, verdict)
                   VALUES (?,?,?,?,?,?, ?,?,?,?, ?,?,?,?,?)""",
                (row["signal_name"], row["horizon"], row["ts"], row["symbol"],
                 row["n_samples"], row["hit_rate"], row["avg_win"],
                 row["avg_loss"], row["expectancy"], row["expectancy_net"],
                 row["sharpe"], row["max_dd"], row["profit_factor"],
                 row["stability"], row["verdict"]))
    conn.commit()

    print(f"  tested {len(SIGNALS)} signals x {len(HORIZONS)} horizons "
          f"in {time.time()-t0:.1f}s")
    print()
    return results


# ------------------------------------------------------------------
# printing
# ------------------------------------------------------------------

def print_ranking(results, top=40):
    if not results:
        print("  no results")
        return

    df = pd.DataFrame(results)

    # drop weak/noise
    keep = df[df["verdict"].isin(["strong", "edge", "edge_short", "weak"])].copy()

    print("=" * 100)
    print("  RANKING BY EXPECTANCY (net of fees)")
    print("=" * 100)
    print()

    # top by net expectancy, per horizon
    for h in ("24h", "4h", "1h"):
        sub = keep[keep["horizon"] == h].sort_values(
            "expectancy_net", ascending=False).head(top)
        if sub.empty:
            continue
        print(f"--- horizon = {h} ---")
        print(f"  {'signal':<28} {'N':>5}  {'hit%':>6}  {'win%':>7}  "
              f"{'loss%':>7}  {'exp%':>7}  {'net%':>7}  "
              f"{'sharpe':>7}  {'stab':>5}  {'verdict':<10}")
        print("  " + "-" * 96)
        for _, r in sub.iterrows():
            print(f"  {r['signal_name']:<28} {r['n_samples']:>5}  "
                  f"{r['hit_rate']*100:>6.1f}  "
                  f"{r['avg_win']*100:>+7.3f}  "
                  f"{r['avg_loss']*100:>+7.3f}  "
                  f"{r['expectancy']*100:>+7.3f}  "
                  f"{r['expectancy_net']*100:>+7.3f}  "
                  f"{r['sharpe']:>+7.2f}  "
                  f"{r['stability']:>5.2f}  {r['verdict']:<10}")
        print()

    # summary
    print("=" * 100)
    print("  SUMMARY")
    print("=" * 100)
    counts = df.groupby(["verdict", "horizon"]).size().unstack(fill_value=0)
    print(counts.to_string())
    print()

    # strongest signal overall
    strong = df[df["verdict"] == "strong"].sort_values(
        "expectancy_net", ascending=False)
    if not strong.empty:
        print("  strongest signals (net expectancy > 0.30%):")
        for _, r in strong.head(10).iterrows():
            print(f"    {r['signal_name']:<30} {r['horizon']:<4} "
                  f"N={r['n_samples']:<5} "
                  f"net={r['expectancy_net']*100:+.3f}%  "
                  f"stab={r['stability']:.2f}")
        print()

    # also show short signals (edge_short)
    shorts = df[df["verdict"] == "edge_short"].sort_values(
        "expectancy_net", ascending=True)
    if not shorts.empty:
        print("  strong SHORT signals (invert these):")
        for _, r in shorts.head(10).iterrows():
            print(f"    {r['signal_name']:<30} {r['horizon']:<4} "
                  f"N={r['n_samples']:<5} "
                  f"net={r['expectancy_net']*100:+.3f}%  "
                  f"stab={r['stability']:.2f}")
        print()


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=str, default="BTCUSDT,ETHUSDT")
    ap.add_argument("--min-samples", type=int, default=20)
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='signal_stats'"
        ).fetchone()
        if not exists:
            print("signal_stats table not found — run: python database/init_db.py")
            return 1

        run_ts = int(time.time() * 1000)
        results = test_all(conn, symbols, args.min_samples, run_ts)
        print_ranking(results)

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
