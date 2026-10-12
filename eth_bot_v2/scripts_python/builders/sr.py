"""Compute support and resistance levels.

Reads ohlcv for a symbol across timeframes. Detects S/R from
8 sources. Writes to sr_levels table.

Usage:
    python -m scripts_python.builders.sr
    python -m scripts_python.builders.sr --symbols BTCUSDT
    python -m scripts_python.builders.sr --timeframes 1h,4h,1d
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
OPT_DB  = ROOT / "database" / "options.db"

DEFAULT_SYMBOLS    = ["BTCUSDT", "ETHUSDT"]
DEFAULT_TIMEFRAMES = ["1h", "4h", "1d"]

# clustering tolerance: 0.3% of price
CLUSTER_TOL = 0.003

# how far back to look for S/R
LOOKBACK_BARS = {
    "1h": 500,     # ~3 weeks
    "4h": 250,     # ~6 weeks
    "1d": 180,     # ~6 months
}


# ------------------------------------------------------------------
# loading
# ------------------------------------------------------------------

def load_ohlcv(conn, symbol, timeframe, limit):
    df = pd.read_sql_query(
        "SELECT open_time, open, high, low, close, volume "
        "FROM ohlcv WHERE symbol=? AND timeframe=? "
        "ORDER BY open_time DESC LIMIT ?",
        conn, params=(symbol, timeframe, limit))
    if df.empty:
        return df
    df = df.sort_values("open_time").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    return df


# ------------------------------------------------------------------
# S/R detection functions
# ------------------------------------------------------------------

def find_swing_points(df, n=2):
    """Local highs/lows: high greater than n bars on each side."""
    highs = []
    lows = []
    h = df["high"].values
    l = df["low"].values
    for i in range(n, len(df) - n):
        if h[i] == max(h[i-n:i+n+1]):
            highs.append(h[i])
        if l[i] == min(l[i-n:i+n+1]):
            lows.append(l[i])
    return highs, lows


def cluster_levels(levels, tol=CLUSTER_TOL):
    """Group nearby levels. Return list of (median_level, touches)."""
    if not levels:
        return []
    s = sorted(levels)
    clusters = []
    current = [s[0]]
    for x in s[1:]:
        if abs(x - current[-1]) / current[-1] <= tol:
            current.append(x)
        else:
            clusters.append(current)
            current = [x]
    clusters.append(current)
    return [(float(np.median(c)), len(c)) for c in clusters]


def find_ma_levels(df):
    """SMA/EMA levels from current bar."""
    levels = []
    last = df.iloc[-1]
    for col in ("sma_20", "sma_50", "sma_200"):
        v = last.get(col)
        if v is not None and pd.notna(v):
            levels.append((float(v), "ma"))
    return levels


def find_volume_nodes(df, bins=30):
    """High-volume price nodes over the window."""
    if df.empty:
        return []
    prices = df["close"].values
    vols = df["volume"].values
    hist, edges = np.histogram(prices, bins=bins, weights=vols)
    if hist.sum() == 0:
        return []
    # take top 5 volume bins
    top_idx = np.argsort(hist)[-5:]
    levels = []
    for i in top_idx:
        center = (edges[i] + edges[i+1]) / 2
        levels.append(float(center))
    return levels


def find_pdh_pdl(conn, symbol):
    """Previous day's high/low, previous week's high/low."""
    out = []
    try:
        df = pd.read_sql_query(
            "SELECT open_time, high, low FROM ohlcv "
            "WHERE symbol=? AND timeframe='1d' ORDER BY open_time DESC LIMIT 15",
            conn, params=(symbol,))
    except Exception:
        return out
    if len(df) < 2:
        return out

    # yesterday
    y = df.iloc[1]   # the last closed day
    out.append((float(y["high"]), "pdh"))
    out.append((float(y["low"]),  "pdh"))

    # previous week: last 7 closed days
    if len(df) >= 8:
        week = df.iloc[1:8]
        out.append((float(week["high"].max()), "pdh"))
        out.append((float(week["low"].min()),  "pdh"))

    # previous month: last 30 closed days
    if len(df) >= 31:
        month = df.iloc[1:31]
        out.append((float(month["high"].max()), "pdh"))
        out.append((float(month["low"].min()),  "pdh"))

    return out


def find_fib_levels(df):
    """Fib retracement from last major swing."""
    if len(df) < 30:
        return []
    lookback = df.tail(60)
    hi = float(lookback["high"].max())
    lo = float(lookback["low"].min())
    if hi <= lo:
        return []
    rng = hi - lo
    # determine direction: was high or low more recent?
    hi_idx = lookback["high"].idxmax()
    lo_idx = lookback["low"].idxmin()
    if hi_idx > lo_idx:
        # uptrend: retracements down from hi
        levels = [hi - rng*r for r in (0.382, 0.5, 0.618)]
    else:
        # downtrend: retracements up from lo
        levels = [lo + rng*r for r in (0.382, 0.5, 0.618)]
    return [(float(x), "fib") for x in levels]


def find_round_levels(price, n=5):
    """Round numbers near current price."""
    step = 50 if price < 5000 else 500
    base = round(price / step) * step
    return [(float(base + i*step), "round") for i in range(-n, n+1)]


def find_options_levels(underlying):
    """Max pain, biggest put OI strike, biggest call OI strike."""
    try:
        conn = sqlite3.connect(OPT_DB)
        df = pd.read_sql_query(
            "SELECT max_pain, put_oi_max_strike, call_oi_max_strike "
            "FROM option_summary WHERE underlying=? ORDER BY ts DESC LIMIT 1",
            conn, params=(underlying,))
        conn.close()
        if df.empty:
            return []
        row = df.iloc[0]
        out = []
        if pd.notna(row.get("max_pain")):
            out.append((float(row["max_pain"]), "options"))
        if pd.notna(row.get("put_oi_max_strike")):
            out.append((float(row["put_oi_max_strike"]), "options"))
        if pd.notna(row.get("call_oi_max_strike")):
            out.append((float(row["call_oi_max_strike"]), "options"))
        return out
    except Exception:
        return []


def find_liq_levels(conn, symbol, price, n=3):
    """Biggest liquidation clusters in last 48h."""
    try:
        df = pd.read_sql_query(
            "SELECT price, value FROM liquidations WHERE symbol=? "
            "ORDER BY ts DESC LIMIT 500",
            conn, params=(symbol,))
        if df.empty:
            return []
    except Exception:
        return []
    # only keep ones within 15% of current price
    df = df[(df["price"] > price*0.85) & (df["price"] < price*1.15)]
    if df.empty:
        return []
    # take top N by value
    df = df.nlargest(n, "value")
    return [(float(r["price"]), "liq") for _, r in df.iterrows()]


# ------------------------------------------------------------------
# main logic per symbol
# ------------------------------------------------------------------

def price_series(conn, symbol, timeframe, limit):
    df = pd.read_sql_query(
        "SELECT open_time, high, low, close FROM ohlcv "
        "WHERE symbol=? AND timeframe=? ORDER BY open_time DESC LIMIT ?",
        conn, params=(symbol, timeframe, limit))
    return df.sort_values("open_time").reset_index(drop=True)


def compute_for_symbol(conn, symbol, timeframe, ts):
    limit = LOOKBACK_BARS.get(timeframe, 200)
    df = load_ohlcv(conn, symbol, timeframe, limit)
    if df.empty or len(df) < 30:
        print(f"    {symbol:<10} {timeframe:<3}  no data")
        return 0

    # load with indicators for MA levels
    df_ind = pd.read_sql_query(
        "SELECT * FROM features WHERE symbol=? ORDER BY ts DESC LIMIT ?",
        conn, params=(symbol, limit))
    df_ind = df_ind.sort_values("ts").reset_index(drop=True)
    if not df_ind.empty:
        df_ind["date"] = pd.to_datetime(df_ind["ts"], unit="ms",
                                        utc=True).dt.tz_convert(None)

    price = float(df["close"].iloc[-1])

    # ---- collect raw levels from all sources
    raw = []  # list of (level, source)

    # 1. swing pivots
    highs, lows = find_swing_points(df, n=2)
    swing_clusters = cluster_levels(highs + lows)
    for lvl, touches in swing_clusters:
        raw.append((lvl, "swing", touches))

    # 2. moving averages
    if not df_ind.empty and timeframe == "1h":
        last = df_ind.iloc[-1]
        for col in ("sma_20", "sma_50", "sma_200"):
            v = last.get(col)
            if v is not None and pd.notna(v):
                raw.append((float(v), "ma", 1))

    # 3. volume nodes
    vol_levels = find_volume_nodes(df)
    for lvl in vol_levels:
        raw.append((lvl, "volume", 1))

    # 4. previous day/week/month high/low
    pdh_levels = find_pdh_pdl(conn, symbol)
    for lvl, src in pdh_levels:
        raw.append((lvl, src, 1))

    # 5. fibonacci
    fib_levels = find_fib_levels(df)
    for lvl, src in fib_levels:
        raw.append((lvl, src, 1))

    # 6. round numbers
    round_levels = find_round_levels(price)
    for lvl, src in round_levels:
        raw.append((lvl, src, 1))

    # 7. options
    underlying = symbol.replace("USDT", "")
    opt_levels = find_options_levels(underlying)
    for lvl, src in opt_levels:
        raw.append((lvl, src, 1))

    # 8. liquidations
    liq_levels = find_liq_levels(conn, symbol, price)
    for lvl, src in liq_levels:
        raw.append((lvl, src, 1))

    # ---- cluster everything
    # first: dedupe per source (keep one entry per source per cluster)
    all_levels = [(lvl, src, touches) for lvl, src, touches in raw]

    # sort by level
    all_levels.sort(key=lambda x: x[0])

    # group: same level within tolerance = same cluster
    clusters = []
    current = []
    for lvl, src, touches in all_levels:
        if not current:
            current = [(lvl, src, touches)]
            continue
        if abs(lvl - current[-1][0]) / current[-1][0] <= CLUSTER_TOL:
            current.append((lvl, src, touches))
        else:
            clusters.append(current)
            current = [(lvl, src, touches)]
    if current:
        clusters.append(current)

    # ---- for each cluster, compute strength + emit rows
    n_written = 0
    for cluster in clusters:
        levels_in = [lvl for lvl, _, _ in cluster]
        sources_in = set(src for _, src, _ in cluster)
        touches_max = max(t for _, _, t in cluster)

        center = float(np.median(levels_in))
        confluence = len(sources_in)

        # distance from current price
        dist_pct = (center - price) / price

        # kind: support if below, resistance if above
        kind = "support" if center < price else "resistance"

        # recency (in ms): use current ts as "now"
        # touches recency: skip for now (would need per-touch scan)
        recency_score = 1.0 if abs(dist_pct) < 0.05 else 0.7

        # strength
        s = 0.4 * min(touches_max, 5) / 5
        s += 0.4 * min(confluence, 5) / 5
        s += 0.2 * recency_score
        s = round(s, 3)

        # write one row per source in this cluster
        for src in sources_in:
            conn.execute(
                """INSERT OR REPLACE INTO sr_levels
                   (symbol, ts, timeframe, level, kind, source,
                    strength, touches, last_test, confluence, distance_pct)
                   VALUES (?,?,?,?,?,?, ?,?,?,?,?)""",
                (symbol, ts, timeframe, center, kind, src,
                 s, touches_max, ts, confluence, dist_pct))
            n_written += 1

    conn.commit()
    print(f"    {symbol:<10} {timeframe:<3}  "
          f"{len(clusters):>3} clusters  {n_written:>4} rows  "
          f"(price {price:,.2f})")
    return n_written


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    ap.add_argument("--timeframes", type=str, default=",".join(DEFAULT_TIMEFRAMES))
    args = ap.parse_args()

    symbols    = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    try:
        # check table exists
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sr_levels'"
        ).fetchone()
        if not exists:
            print("sr_levels table not found — run: python database/init_db.py")
            return 1

        ts = int(time.time() * 1000)
        print("=" * 60)
        print("  COMPUTE S/R LEVELS")
        print("=" * 60)
        print(f"  symbols    : {', '.join(symbols)}")
        print(f"  timeframes : {', '.join(timeframes)}")
        print(f"  tolerance  : {CLUSTER_TOL*100:.1f}%")
        print()

        t0 = time.time()
        total = 0
        for tf in timeframes:
            print(f"[{tf}]")
            for sym in symbols:
                try:
                    n = compute_for_symbol(conn, sym, tf, ts)
                    total += n
                except Exception as e:
                    print(f"    {sym} FAIL: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
            print()

        elapsed = time.time() - t0
        print("=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(f"  rows written: {total}")
        print(f"  time        : {elapsed:.1f}s")

        # top levels per symbol/timeframe
        print()
        print("  top levels (by strength):")
        for sym in symbols:
            for tf in timeframes:
                rows = conn.execute(
                    """SELECT level, kind, MAX(strength), MAX(confluence)
                       FROM sr_levels
                       WHERE symbol=? AND timeframe=? AND ts=?
                       GROUP BY level
                       ORDER BY MAX(strength) DESC LIMIT 5""",
                    (sym, tf, ts)).fetchall()
                if not rows:
                    continue
                print(f"    {sym} {tf}:")
                for lvl, kind, strength, conf in rows:
                    print(f"      {lvl:>12,.2f}  {kind:<10}  "
                          f"strength={strength:.2f}  conf={conf}")

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
