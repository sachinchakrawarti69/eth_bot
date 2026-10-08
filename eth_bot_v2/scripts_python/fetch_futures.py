"""Fetch USD-M futures ohlcv for BTCUSDT and ETHUSDT.

Adds symbols BTCUSDT and ETHUSDT (same as spot names - the DB
stores futures and spot together, distinguished by .P suffix
in a future version).

For now, futures data uses the same symbol names. If you also
have spot, use "--market spot" to write spot instead.

Usage:
    python -m scripts_python.fetch_futures                    # both symbols, 1h+4h+1d
    python -m scripts_python.fetch_futures --symbols ETHUSDT
    python -m scripts_python.fetch_futures --timeframes 1h
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"

FUTURES_BASE = "https://fapi.binance.com"

DEFAULT_SYMBOLS    = ["BTCUSDT", "ETHUSDT"]
DEFAULT_TIMEFRAMES = ["1h", "4h", "1d"]

BATCH_LIMIT = 1500

INTERVAL_MS = {
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}

BACKFILL_DAYS = {
    "1h": 730,
    "4h": 730,
    "1d": 2190,
}


def req(path, params=None, timeout=20):
    url = f"{FUTURES_BASE}{path}"
    r = requests.get(url, params=params or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def last_open_time(conn, symbol, interval):
    row = conn.execute(
        "SELECT MAX(open_time) FROM ohlcv WHERE symbol=? AND timeframe=?",
        (symbol, interval)).fetchone()
    return row[0] if row and row[0] is not None else None


def count_rows(conn, symbol, interval):
    return conn.execute(
        "SELECT COUNT(*) FROM ohlcv WHERE symbol=? AND timeframe=?",
        (symbol, interval)).fetchone()[0]


def upsert(conn, symbol, interval, rows):
    conn.executemany(
        """INSERT INTO ohlcv
           (symbol, timeframe, open_time, close_time, open, high, low,
            close, volume, quote_volume, trades)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(symbol, timeframe, open_time) DO UPDATE SET
             close_time=excluded.close_time, open=excluded.open,
             high=excluded.high, low=excluded.low, close=excluded.close,
             volume=excluded.volume, quote_volume=excluded.quote_volume,
             trades=excluded.trades""",
        [(symbol, interval, int(k[0]), int(k[6]),
          float(k[1]), float(k[2]), float(k[3]), float(k[4]),
          float(k[5]), float(k[7]), int(k[8])) for k in rows])
    conn.commit()


def fetch_symbol(conn, symbol, interval, days=None):
    step_ms = INTERVAL_MS[interval]
    days = days or BACKFILL_DAYS.get(interval, 365)

    before = count_rows(conn, symbol, interval)
    last = last_open_time(conn, symbol, interval)

    if last is not None:
        start_ms = last + step_ms
        origin = "resume"
    else:
        start_ms = int((datetime.now(timezone.utc)
                        - timedelta(days=days)).timestamp() * 1000)
        origin = "backfill"

    now_ms = int(time.time() * 1000)
    expected = max(0, (now_ms - start_ms) // step_ms)

    print(f"  {symbol:<10} {interval:<3}  {origin:<8}  expected ~{expected:>5}")

    total = 0
    cursor = start_ms
    while True:
        batch = req("/fapi/v1/klines", {
            "symbol": symbol,
            "interval": interval,
            "startTime": cursor,
            "limit": BATCH_LIMIT,
        })
        if not batch:
            break
        batch = [k for k in batch if int(k[6]) < now_ms]
        if not batch:
            break
        upsert(conn, symbol, interval, batch)
        total += len(batch)
        if len(batch) < BATCH_LIMIT:
            break
        cursor = batch[-1][0] + step_ms
        time.sleep(0.2)

    after = count_rows(conn, symbol, interval)
    print(f"               -> +{total} rows  ({before} -> {after})")
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    ap.add_argument("--timeframes", type=str, default=",".join(DEFAULT_TIMEFRAMES))
    args = ap.parse_args()

    symbols    = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        print("Run: python database/init_db.py")
        return 1

    print("=" * 60)
    print("  FETCH FUTURES (USD-M)")
    print("=" * 60)
    print(f"  symbols    : {', '.join(symbols)}")
    print(f"  timeframes : {', '.join(timeframes)}")
    print()

    conn = sqlite3.connect(DB_PATH)
    try:
        for tf in timeframes:
            if tf not in INTERVAL_MS:
                print(f"skipping {tf}")
                continue
            print(f"[{tf}]")
            for sym in symbols:
                try:
                    fetch_symbol(conn, sym, tf)
                except Exception as e:
                    print(f"  {sym:<10} FAIL: {type(e).__name__}: {e}")
            print()

        print("=" * 60)
        print("  ROWS IN ohlcv")
        print("=" * 60)
        rows = conn.execute(
            "SELECT symbol, timeframe, COUNT(*) FROM ohlcv "
            "GROUP BY symbol, timeframe ORDER BY symbol, timeframe").fetchall()
        for sym, tf, n in rows:
            print(f"  {sym:<10} {tf:<3} {n:>7}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
