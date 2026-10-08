"""Fetch taker buy/sell volume from Binance USD-M futures.

Usage:
    python -m scripts_python.fetch_taker
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
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]


def req(path, params=None, timeout=20):
    r = requests.get(f"{FUTURES_BASE}{path}", params=params or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def last_ts(conn, symbol):
    try:
        row = conn.execute(
            "SELECT MAX(ts) FROM taker_volume WHERE symbol=?", (symbol,)).fetchone()
        return row[0] if row and row[0] is not None else None
    except Exception:
        return None


def count_rows(conn, symbol):
    return conn.execute(
        "SELECT COUNT(*) FROM taker_volume WHERE symbol=?", (symbol,)).fetchone()[0]


def upsert(conn, symbol, rows):
    conn.executemany(
        """INSERT INTO taker_volume (symbol, ts, taker_buy, taker_sell, buy_ratio)
           VALUES (?,?,?,?,?)
           ON CONFLICT(symbol, ts) DO UPDATE SET
             taker_buy=excluded.taker_buy,
             taker_sell=excluded.taker_sell,
             buy_ratio=excluded.buy_ratio""",
        [(symbol, int(r["timestamp"]),
          float(r["buyVol"]), float(r["sellVol"]),
          float(r["buySellRatio"])) for r in rows])
    conn.commit()


def fetch_symbol(conn, symbol):
    before = count_rows(conn, symbol)
    last = last_ts(conn, symbol)

    if last is not None:
        start_ms = last + 1
        origin = "resume"
    else:
        start_ms = int((datetime.now(timezone.utc)
                        - timedelta(days=29)).timestamp() * 1000)
        origin = "backfill"

    print(f"  {symbol:<10} {origin:<8}")

    total = 0
    cursor = start_ms
    while True:
        batch = req("/futures/data/takerlongshortRatio", {
            "symbol": symbol,
            "period": "1h",
            "startTime": cursor,
            "limit": 500,
        })
        if not batch:
            break
        upsert(conn, symbol, batch)
        total += len(batch)
        if len(batch) < 500:
            break
        cursor = int(batch[-1]["timestamp"]) + 1
        time.sleep(0.2)

    after = count_rows(conn, symbol)
    print(f"               -> +{total} rows  ({before} -> {after})")
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    args = ap.parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    print("=" * 60)
    print("  FETCH TAKER VOLUME")
    print("=" * 60)
    print(f"  symbols: {', '.join(symbols)}")
    print()

    conn = sqlite3.connect(DB_PATH)
    try:
        for sym in symbols:
            try:
                fetch_symbol(conn, sym)
            except Exception as e:
                print(f"  {sym} FAIL: {type(e).__name__}: {e}")
        print()
        print("  totals:")
        for sym in symbols:
            try:
                print(f"    {sym:<10} {count_rows(conn, sym):>6}")
            except Exception:
                print(f"    {sym:<10} (no table)")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
