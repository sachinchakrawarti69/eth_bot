"""Fetch intraday ETHUSDT candles into market.db."""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from database.config.api.binance import get_klines

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"
SYMBOL = "ETHUSDT"
BATCH_LIMIT = 1000

INTERVAL_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


def last_open_time(conn, interval):
    row = conn.execute(
        "SELECT MAX(open_time) FROM ohlcv WHERE symbol=? AND timeframe=?",
        (SYMBOL, interval)).fetchone()
    return row[0] if row and row[0] is not None else None


def count_rows(conn, interval):
    return conn.execute(
        "SELECT COUNT(*) FROM ohlcv WHERE symbol=? AND timeframe=?",
        (SYMBOL, interval)).fetchone()[0]


def upsert(conn, interval, rows):
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
        [(SYMBOL, interval, int(k[0]), int(k[6]),
          float(k[1]), float(k[2]), float(k[3]), float(k[4]),
          float(k[5]), float(k[7]), int(k[8])) for k in rows])
    conn.commit()


def fetch_interval(interval, days):
    if interval not in INTERVAL_MS:
        raise ValueError(f"unsupported interval: {interval}")
    step_ms = INTERVAL_MS[interval]

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return 0

    conn = sqlite3.connect(DB_PATH)
    try:
        before = count_rows(conn, interval)
        last = last_open_time(conn, interval)
        if last is not None:
            start_ms = last + step_ms
            origin = "resume"
        else:
            start_ms = int((datetime.now(timezone.utc)
                            - timedelta(days=days)).timestamp() * 1000)
            origin = "backfill"

        now_ms = int(time.time() * 1000)
        expected = max(0, (now_ms - start_ms) // step_ms)

        print(f"symbol    : {SYMBOL}")
        print(f"interval  : {interval}")
        print(f"origin    : {origin}")
        print(f"start     : {datetime.fromtimestamp(start_ms/1000, tz=timezone.utc)}")
        print(f"expected  : ~{expected} new candles")
        print()

        total = 0
        cursor = start_ms
        while True:
            batch = get_klines(SYMBOL, interval, start_ms=cursor, limit=BATCH_LIMIT)
            if not batch:
                break
            batch = [k for k in batch if int(k[6]) < now_ms]
            if not batch:
                break
            upsert(conn, interval, batch)
            total += len(batch)
            d = datetime.fromtimestamp(batch[-1][0] / 1000, tz=timezone.utc)
            print(f"  ...fetched {total:>5} rows, up to {d:%Y-%m-%d %H:%M}")
            if len(batch) < BATCH_LIMIT:
                break
            cursor = batch[-1][0] + step_ms
            time.sleep(0.25)

        after = count_rows(conn, interval)
        print()
        print(f"done      : +{total} rows  ({before} -> {after})")
        return total
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", default="1h", choices=list(INTERVAL_MS))
    ap.add_argument("--days", type=int, default=730)
    args = ap.parse_args()
    fetch_interval(args.interval, args.days)
    return 0


if __name__ == "__main__":
    sys.exit(main())