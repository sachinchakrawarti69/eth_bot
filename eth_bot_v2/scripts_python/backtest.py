"""Backtest strategies derived from Phase 4 signals."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"
ROUND_TRIP_FEE = 0.0010


STRATEGIES = {
    "mean_reversion": {
        "desc": "Buy when 4h RSI < 30, hold 24h",
        "entry": lambda d: d["rsi_14_4h"] < 30,
        "direction": "long",
        "exit": {"type": "fixed_hold", "bars": 24},
    },
    "trend_follow": {
        "desc": "Buy when regime bull AND macd_4h > 0, hold 24h",
        "entry": lambda d: (d["regime"] == "bull") & (d["macd_hist_4h"] > 0),
        "direction": "long",
        "exit": {"type": "fixed_hold", "bars": 24},
    },
    "fade_longs": {
        "desc": "Short when ls_ratio > 1.5, hold 24h",
        "entry": lambda d: d["ls_ratio"] > 1.5,
        "direction": "short",
        "exit": {"type": "fixed_hold", "bars": 24},
    },
    "fade_funding": {
        "desc": "Short when funding > 0.05%, hold 24h",
        "entry": lambda d: d["funding"] > 0.0005,
        "direction": "short",
        "exit": {"type": "fixed_hold", "bars": 24},
    },
    "bull_dip": {
        "desc": "Buy when regime bull AND rsi_1h < 30, hold 24h",
        "entry": lambda d: (d["regime"] == "bull") & (d["rsi_14"] < 30),
        "direction": "long",
        "exit": {"type": "fixed_hold", "bars": 24},
    },
    "bull_dip_st": {
        "desc": "Same entry, exit on 2% stop / 4% target / 24h max",
        "entry": lambda d: (d["regime"] == "bull") & (d["rsi_14"] < 30),
        "direction": "long",
        "exit": {"type": "stop_target", "stop_pct": 0.02,
                 "target_pct": 0.04, "max_bars": 24},
    },
    "hour_18_long": {
        "desc": "Buy at 18 UTC if rsi_1h < 40, hold 4h",
        "entry": lambda d: (d["hour"] == 18) & (d["rsi_14"] < 40),
        "direction": "long",
        "exit": {"type": "fixed_hold", "bars": 4},
    },
    "rsi_oversold": {
        "desc": "Buy when 1h RSI < 25, hold 12h",
        "entry": lambda d: d["rsi_14"] < 25,
        "direction": "long",
        "exit": {"type": "fixed_hold", "bars": 12},
    },
}


def load_features(conn, symbols):
    placeholders = ",".join("?" * len(symbols))
    df = pd.read_sql_query(
        f"SELECT * FROM features WHERE symbol IN ({placeholders}) "
        f"ORDER BY symbol, ts",
        conn, params=symbols)
    return df


def simulate_trade(df_symbol, entry_idx, strategy):
    entry_row = df_symbol.iloc[entry_idx]
    entry_price = float(entry_row["close"])
    entry_ts = int(entry_row["ts"])

    exit_spec = strategy["exit"]
    direction = strategy["direction"]
    mult = 1 if direction == "long" else -1

    if exit_spec["type"] == "fixed_hold":
        bars = exit_spec["bars"]
        exit_idx = entry_idx + bars
        if exit_idx >= len(df_symbol):
            return None
        exit_row = df_symbol.iloc[exit_idx]
        exit_price = float(exit_row["close"])
        ret_gross = (exit_price / entry_price - 1) * mult
        return {
            "entry_ts": entry_ts,
            "exit_ts": int(exit_row["ts"]),
            "entry_price": entry_price,
            "exit_price": exit_price,
            "return_gross": ret_gross,
            "reason_exit": f"time_{bars}h",
        }

    if exit_spec["type"] == "stop_target":
        stop_pct = exit_spec["stop_pct"]
        target_pct = exit_spec["target_pct"]
        max_bars = exit_spec["max_bars"]

        if direction == "long":
            stop_level = entry_price * (1 - stop_pct)
            target_level = entry_price * (1 + target_pct)
        else:
            stop_level = entry_price * (1 + stop_pct)
            target_level = entry_price * (1 - target_pct)

        for i in range(1, max_bars + 1):
            idx = entry_idx + i
            if idx >= len(df_symbol):
                break
            row = df_symbol.iloc[idx]
            high = float(row["high"])
            low = float(row["low"])

            if direction == "long":
                if low <= stop_level:
                    return {"entry_ts": entry_ts, "exit_ts": int(row["ts"]),
                            "entry_price": entry_price, "exit_price": stop_level,
                            "return_gross": -stop_pct, "reason_exit": "stop"}
                if high >= target_level:
                    return {"entry_ts": entry_ts, "exit_ts": int(row["ts"]),
                            "entry_price": entry_price, "exit_price": target_level,
                            "return_gross": target_pct, "reason_exit": "target"}
            else:
                if high >= stop_level:
                    return {"entry_ts": entry_ts, "exit_ts": int(row["ts"]),
                            "entry_price": entry_price, "exit_price": stop_level,
                            "return_gross": -stop_pct, "reason_exit": "stop"}
                if low <= target_level:
                    return {"entry_ts": entry_ts, "exit_ts": int(row["ts"]),
                            "entry_price": entry_price, "exit_price": target_level,
                            "return_gross": target_pct, "reason_exit": "target"}

        last_idx = min(entry_idx + max_bars, len(df_symbol) - 1)
        last_row = df_symbol.iloc[last_idx]
        exit_price = float(last_row["close"])
        ret_gross = (exit_price / entry_price - 1) * mult
        return {"entry_ts": entry_ts, "exit_ts": int(last_row["ts"]),
                "entry_price": entry_price, "exit_price": exit_price,
                "return_gross": ret_gross, "reason_exit": f"time_{max_bars}h"}

    return None


def backtest_strategy(df, strategy):
    trades = []
    for symbol in df["symbol"].unique():
        sub = df[df["symbol"] == symbol].reset_index(drop=True)
        try:
            entries = strategy["entry"](sub)
        except Exception as e:
            print(f"    {symbol}: {e}")
            continue
        i = 0
        while i < len(sub):
            if entries.iloc[i]:
                trade = simulate_trade(sub, i, strategy)
                if trade:
                    trade["symbol"] = symbol
                    trades.append(trade)
                i += 1
            else:
                i += 1
    return trades


def compute_metrics(trades):
    if not trades:
        return None
    tdf = pd.DataFrame(trades)
    tdf["return_net"] = tdf["return_gross"] - ROUND_TRIP_FEE

    wins = tdf[tdf["return_net"] > 0]
    losses = tdf[tdf["return_net"] <= 0]

    n = len(tdf)
    hit = len(wins) / n
    avg_win = float(wins["return_net"].mean()) if len(wins) else 0.0
    avg_loss = float(losses["return_net"].mean()) if len(losses) else 0.0
    exp = hit * avg_win + (1 - hit) * avg_loss

    tdf["entry_year"] = pd.to_datetime(tdf["entry_ts"], unit="ms", utc=True).dt.year
    year_stats = []
    for y, grp in tdf.groupby("entry_year"):
        w = grp[grp["return_net"] > 0]
        l = grp[grp["return_net"] <= 0]
        hr = len(w) / len(grp)
        aw = float(w["return_net"].mean()) if len(w) else 0.0
        al = float(l["return_net"].mean()) if len(l) else 0.0
        e = hr * aw + (1 - hr) * al
        year_stats.append({"year": int(y), "n": len(grp), "expectancy": e})

    cum = (1 + tdf["return_net"]).cumprod()
    total_return = float(cum.iloc[-1] - 1) if len(cum) else 0.0
    dd = float((cum / cum.cummax() - 1).min()) if len(cum) else 0.0

    tpy = n / max(1, len(year_stats))
    sharpe = (exp / tdf["return_net"].std(ddof=0) * np.sqrt(tpy)
              if tdf["return_net"].std(ddof=0) > 0 else 0.0)

    gw = float(wins["return_net"].sum()) if len(wins) else 0.0
    gl = abs(float(losses["return_net"].sum())) if len(losses) else 0.0
    pf = gw / gl if gl > 0 else 999.0
    pos_years = sum(1 for y in year_stats if y["expectancy"] > 0)

    return {
        "n": n, "hit_rate": hit, "avg_win": avg_win, "avg_loss": avg_loss,
        "expectancy": exp, "total_return": total_return, "max_dd": dd,
        "sharpe": sharpe, "profit_factor": pf,
        "n_years_pos": pos_years, "n_years_total": len(year_stats),
        "year_stats": year_stats, "trades_df": tdf,
    }


def verdict(m):
    if m is None: return "no trades"
    net = m["expectancy"]
    if net > 0.003 and m["sharpe"] > 1.0 and m["n_years_pos"] >= m["n_years_total"] * 0.6:
        return "strong"
    if net > 0.001 and m["sharpe"] > 0.5:
        return "edge"
    if net > 0:
        return "weak"
    return "none"


def run_strategy(conn, name, strategy, df, run_ts):
    print(f"\n[{name}]")
    print(f"  {strategy['desc']}")
    trades = backtest_strategy(df, strategy)
    m = compute_metrics(trades)
    if m is None:
        print("  no trades")
        return
    v = verdict(m)
    print(f"  trades       : {m['n']}")
    print(f"  hit rate     : {m['hit_rate']*100:.1f}%")
    print(f"  avg win      : {m['avg_win']*100:+.3f}%")
    print(f"  avg loss     : {m['avg_loss']*100:+.3f}%")
    print(f"  expectancy   : {m['expectancy']*100:+.3f}%")
    print(f"  total return : {m['total_return']*100:+.1f}%")
    print(f"  max DD       : {m['max_dd']*100:.1f}%")
    print(f"  sharpe       : {m['sharpe']:.2f}")
    print(f"  profit factor: {m['profit_factor']:.2f}")
    print(f"  years +      : {m['n_years_pos']}/{m['n_years_total']}")
    print(f"  verdict      : {v}")
    for y in m["year_stats"]:
        print(f"    {y['year']}  N={y['n']:>4}  exp={y['expectancy']*100:+.3f}%")

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO backtest_runs
           (name, strategy, ts, symbols, start_ts, end_ts,
            n_trades, win_rate, avg_win, avg_loss, expectancy,
            expectancy_net, total_return, sharpe, max_dd, profit_factor,
            n_years_pos, n_years_total, verdict)
           VALUES (?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?,?, ?,?,?)""",
        (name, json.dumps({"desc": strategy["desc"]}), run_ts,
         ",".join(df["symbol"].unique()),
         int(df["ts"].min()), int(df["ts"].max()),
         m["n"], m["hit_rate"], m["avg_win"], m["avg_loss"],
         m["expectancy"], m["expectancy"], m["total_return"],
         m["sharpe"], m["max_dd"], m["profit_factor"],
         m["n_years_pos"], m["n_years_total"], v))
    run_id = cur.lastrowid

    for _, t in m["trades_df"].iterrows():
        cur.execute(
            """INSERT INTO backtest_trades
               (run_id, symbol, entry_ts, exit_ts, direction,
                entry_price, exit_price, return_gross, return_net,
                reason_entry, reason_exit, signal_name)
               VALUES (?,?,?,?,?, ?,?,?,?, ?,?,?)""",
            (run_id, t["symbol"], int(t["entry_ts"]), int(t["exit_ts"]),
             strategy["direction"], float(t["entry_price"]),
             float(t["exit_price"]), float(t["return_gross"]),
             float(t["return_net"]), strategy["desc"],
             t["reason_exit"], name))
    conn.commit()
    print(f"  saved run_id={run_id}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=str, default="BTCUSDT,ETHUSDT")
    ap.add_argument("--strategy", type=str, default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        print("strategies:")
        for k, v in STRATEGIES.items():
            print(f"  {k:<20} {v['desc']}")
        return 0

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    conn = sqlite3.connect(DB_PATH)
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='backtest_runs'"
        ).fetchone()
        if not exists:
            print("backtest_runs table not found - run: python database/init_db.py")
            return 1

        df = load_features(conn, symbols)
        if df.empty:
            print("no features data")
            return 1

        print("=" * 70)
        print("  BACKTEST")
        print("=" * 70)
        print(f"  symbols  : {', '.join(symbols)}")
        print(f"  rows     : {len(df):,}")
        print(f"  fee/trip : {ROUND_TRIP_FEE*100:.2f}%")

        run_ts = int(time.time() * 1000)

        if args.strategy:
            if args.strategy not in STRATEGIES:
                print(f"unknown: {args.strategy}")
                return 1
            run_strategy(conn, args.strategy, STRATEGIES[args.strategy], df, run_ts)
        else:
            for name, strat in STRATEGIES.items():
                run_strategy(conn, name, strat, df, run_ts)

        print()
        print("=" * 70)
        print("  SUMMARY")
        print("=" * 70)
        rows = conn.execute(
            """SELECT name, n_trades, expectancy*100, sharpe, verdict
               FROM backtest_runs WHERE ts=?
               ORDER BY expectancy DESC""", (run_ts,)).fetchall()
        print(f"  {'strategy':<20} {'N':>5}  {'exp%':>7}  {'sharpe':>7}  {'verdict':<10}")
        print("  " + "-" * 60)
        for name, n, exp, sh, v in rows:
            print(f"  {name:<20} {n:>5}  {exp:>+7.3f}  {sh:>+7.2f}  {v:<10}")

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
