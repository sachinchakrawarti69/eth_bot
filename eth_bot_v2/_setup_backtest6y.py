"""Create 6-year backtest files: bt6/ package + runner."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
BT   = ROOT / "bt6"
BT.mkdir(exist_ok=True)

INIT = '"""6-year backtest."""\n'


# ================================================================
#  bt6/data.py
# ================================================================

DATA = '''"""Load 6 years of daily features + candles."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"


def load_daily(symbol="ETHUSDT"):
    """Return daily OHLCV + indicators from the ohlcv table.

    This uses the ohlcv table directly (6 years of 1d bars)
    because the features table only has ~2 years of 1h rows.
    """
    with sqlite3.connect(DB_PATH) as c:
        df = pd.read_sql_query(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlcv WHERE symbol=? AND timeframe='1d' "
            "ORDER BY open_time",
            c, params=(symbol,))
    if df.empty:
        raise RuntimeError("no daily ohlcv for " + symbol)

    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.drop(columns=["open_time"]).set_index("date")

    # indicators
    df["ret_1"]  = df["close"].pct_change()
    df["ret_5"]  = df["close"].pct_change(5)
    df["ret_20"] = df["close"].pct_change(20)
    df["vol_20"] = df["ret_1"].rolling(20).std()
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["sma_200"]= df["close"].rolling(200).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()
    macd = df["ema_12"] - df["ema_26"]
    df["macd"]      = macd
    df["macd_sig"]  = macd.ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

    d  = df["close"].diff()
    up = d.clip(lower=0).rolling(14).mean()
    dn = (-d.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - 100 / (1 + up / dn.replace(0, float("nan")))

    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"]  - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()

    df["trend_up"]   = ((df["close"] > df["sma_50"]) & (df["sma_50"] > df["sma_200"])).astype(int)
    df["trend_down"] = ((df["close"] < df["sma_50"]) & (df["sma_50"] < df["sma_200"])).astype(int)

    def regime(row):
        if row["trend_up"] == 1:   return "bull"
        if row["trend_down"] == 1: return "bear"
        return "chop"

    df["regime"] = df.apply(regime, axis=1)
    df["dist_sma50"] = (df["close"] - df["sma_50"]) / df["sma_50"]

    return df.dropna(subset=["sma_200"])
'''


# ================================================================
#  bt6/strategies.py
# ================================================================

STRATS = '''"""Strategy definitions for the 6-year backtest."""

from __future__ import annotations


STRATEGIES = {
    "rsi_oversold_25": {
        "desc": "Buy when 1d RSI < 25, hold 14 days",
        "entry": lambda df: df["rsi_14"] < 25,
        "direction": "long",
        "hold_days": 14,
    },
    "rsi_oversold_30": {
        "desc": "Buy when 1d RSI < 30, hold 14 days",
        "entry": lambda df: df["rsi_14"] < 30,
        "direction": "long",
        "hold_days": 14,
    },
    "rsi_overbought_70": {
        "desc": "Short when 1d RSI > 70, hold 14 days",
        "entry": lambda df: df["rsi_14"] > 70,
        "direction": "short",
        "hold_days": 14,
    },
    "bull_dip": {
        "desc": "Buy when regime bull AND RSI < 40, hold 14 days",
        "entry": lambda df: (df["regime"] == "bull") & (df["rsi_14"] < 40),
        "direction": "long",
        "hold_days": 14,
    },
    "bear_rally": {
        "desc": "Short when regime bear AND RSI > 60, hold 14 days",
        "entry": lambda df: (df["regime"] == "bear") & (df["rsi_14"] > 60),
        "direction": "short",
        "hold_days": 14,
    },
    "trend_follow": {
        "desc": "Buy when regime bull AND MACD hist > 0, hold 30 days",
        "entry": lambda df: (df["regime"] == "bull") & (df["macd_hist"] > 0),
        "direction": "long",
        "hold_days": 30,
    },
    "fade_extended": {
        "desc": "Short when close > +15% from SMA50, hold 14 days",
        "entry": lambda df: df["dist_sma50"] > 0.15,
        "direction": "short",
        "hold_days": 14,
    },
    "buy_capitulation": {
        "desc": "Buy when vol_20 > 2x median AND RSI < 35, hold 14 days",
        "entry": lambda df: (df["vol_20"] > 2 * df["vol_20"].rolling(90).median()) & (df["rsi_14"] < 35),
        "direction": "long",
        "hold_days": 14,
    },
}
'''


# ================================================================
#  bt6/engine.py
# ================================================================

ENGINE = '''"""Backtest engine with realistic fees."""

from __future__ import annotations
import numpy as np
import pandas as pd


ROUND_TRIP_FEE = 0.0010   # 0.10% per side, taker


def simulate(df, strategy):
    """Return list of trades for a given strategy."""
    entry_mask = strategy["entry"](df)
    direction  = strategy["direction"]
    hold       = strategy["hold_days"]
    mult       = 1 if direction == "long" else -1

    trades = []
    i = 0
    n = len(df)
    while i < n:
        if bool(entry_mask.iloc[i]):
            entry_price = float(df["close"].iloc[i])
            entry_date  = df.index[i]
            exit_idx    = i + hold
            if exit_idx >= n:
                break
            exit_price  = float(df["close"].iloc[exit_idx])
            exit_date   = df.index[exit_idx]

            gross = (exit_price / entry_price - 1) * mult
            net   = gross - ROUND_TRIP_FEE

            trades.append({
                "entry_date":  entry_date,
                "exit_date":   exit_date,
                "entry_price": entry_price,
                "exit_price":  exit_price,
                "return_gross": gross,
                "return_net":   net,
                "direction":   direction,
            })
            i += 1     # no overlapping trades
        else:
            i += 1
    return trades


def metrics(trades):
    if not trades:
        return None
    t = pd.DataFrame(trades)
    n = len(t)
    wins = t[t["return_net"] > 0]
    losses = t[t["return_net"] <= 0]

    hit = len(wins) / n
    avg_win = float(wins["return_net"].mean()) if len(wins) else 0.0
    avg_loss = float(losses["return_net"].mean()) if len(losses) else 0.0
    exp = hit * avg_win + (1 - hit) * avg_loss

    cum = (1 + t["return_net"]).cumprod()
    total = float(cum.iloc[-1] - 1) if len(cum) else 0.0
    dd = float((cum / cum.cummax() - 1).min()) if len(cum) else 0.0

    # Sharpe per trade, annualized by trades/year
    t["entry_year"] = pd.to_datetime(t["entry_date"]).dt.year
    years = t["entry_year"].nunique() or 1
    tpy = n / years
    vol = t["return_net"].std(ddof=0)
    sharpe = float(exp / vol * np.sqrt(tpy)) if vol > 0 else 0.0

    gw = float(wins["return_net"].sum()) if len(wins) else 0.0
    gl = abs(float(losses["return_net"].sum())) if len(losses) else 0.0
    pf = gw / gl if gl > 0 else float("inf")

    # per-year
    by_year = []
    for y, g in t.groupby("entry_year"):
        w = g[g["return_net"] > 0]
        l = g[g["return_net"] <= 0]
        hr = len(w) / len(g)
        aw = float(w["return_net"].mean()) if len(w) else 0.0
        al = float(l["return_net"].mean()) if len(l) else 0.0
        e = hr * aw + (1 - hr) * al
        cum_year = float((1 + g["return_net"]).prod() - 1)
        by_year.append({
            "year": int(y),
            "n": len(g),
            "hit": hr,
            "expectancy": e,
            "total_return": cum_year,
        })

    pos_years = sum(1 for y in by_year if y["total_return"] > 0)

    return {
        "n": n,
        "hit_rate": hit,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": exp,
        "total_return": total,
        "max_dd": dd,
        "sharpe": sharpe,
        "profit_factor": pf if pf != float("inf") else 999.0,
        "by_year": by_year,
        "pos_years": pos_years,
        "total_years": len(by_year),
        "trades_df": t,
    }


def verdict(m):
    if m is None: return "no trades"
    if m["n"] < 10: return "too few"
    if m["expectancy"] > 0.005 and m["sharpe"] > 0.8 and m["pos_years"] >= m["total_years"] * 0.6:
        return "strong"
    if m["expectancy"] > 0.001 and m["sharpe"] > 0.3:
        return "edge"
    if m["expectancy"] > 0:
        return "weak"
    return "none"
'''


# ================================================================
#  bt6/run.py
# ================================================================

RUN = '''"""Run the 6-year backtest.

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
'''


# ================================================================
#  WRITE
# ================================================================

FILES = {
    BT / "__init__.py":    INIT,
    BT / "data.py":        DATA,
    BT / "strategies.py":  STRATS,
    BT / "engine.py":      ENGINE,
    BT / "run.py":         RUN,
}


def main():
    print("=" * 60)
    print("  SETUP 6-YEAR BACKTEST")
    print("=" * 60)
    print()

    for path, content in FILES.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print("  wrote " + str(path.relative_to(ROOT)) +
              "  (" + str(content.count(chr(10)) + 1) + " lines)")

    # syntax check
    print()
    print("  verifying syntax...")
    import ast
    for path in FILES:
        ast.parse(path.read_text(encoding="utf-8"))
        print("  OK " + path.name)

    print()
    print("=" * 60)
    print("  NEXT")
    print("=" * 60)
    print()
    print("  python -m bt6.run")
    print("  python -m bt6.run --symbol BTCUSDT")
    print("  python -m bt6.run --symbols BTCUSDT,ETHUSDT")
    print()


if __name__ == "__main__":
    main()