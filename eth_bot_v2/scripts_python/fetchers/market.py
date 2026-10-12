"""Fetch ETHUSDT 1-day candles into market.db (gap-filling)."""

import sqlite3, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from database.config.api.binance import get_klines

ROOT          = Path(__file__).resolve().parents[1]
DB_PATH       = ROOT / "database" / "market.db"
SYMBOL        = "ETHUSDT"
TIMEFRAME     = "1d"
DAY_MS        = 86_400_000
DEFAULT_YEARS = 6
BATCH_LIMIT   = 1000


def last_open_time(conn):
    r = conn.execute("SELECT MAX(open_time) FROM ohlcv WHERE symbol=? AND timeframe=?",
                     (SYMBOL, TIMEFRAME)).fetchone()
    return r[0] if r and r[0] is not None else None


def count_rows(conn):
    r = conn.execute("SELECT COUNT(*) FROM ohlcv WHERE symbol=? AND timeframe=?",
                     (SYMBOL, TIMEFRAME)).fetchone()
    return r[0] if r else 0


def upsert(conn, rows):
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
        [(SYMBOL, TIMEFRAME, int(k[0]), int(k[6]),
          float(k[1]), float(k[2]), float(k[3]), float(k[4]),
          float(k[5]), float(k[7]), int(k[8])) for k in rows],
    )
    conn.commit()


def ms_of(dt): return int(dt.timestamp() * 1000)


def resolve_start(conn):
    last = last_open_time(conn)
    if last is not None:
        return last + DAY_MS
    return ms_of(datetime.now(timezone.utc) - timedelta(days=365 * DEFAULT_YEARS))


def fetch_all(start_ms):
    rows, cursor = [], start_ms
    now_ms = int(time.time() * 1000)
    while True:
        batch = get_klines(SYMBOL, TIMEFRAME, start_ms=cursor, limit=BATCH_LIMIT)
        if not batch:
            break
        batch = [k for k in batch if int(k[6]) < now_ms]
        if not batch:
            break
        rows.extend(batch)
        d = datetime.fromtimestamp(batch[-1][0] / 1000, tz=timezone.utc).date()
        print(f"  ...fetched {len(rows):>5} rows, up to {d}", flush=True)
        if len(batch) < BATCH_LIMIT:
            break
        cursor = batch[-1][0] + DAY_MS
        time.sleep(0.25)
    return rows


def update():
    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return 1
    conn = sqlite3.connect(DB_PATH)
    try:
        before   = count_rows(conn)
        start_ms = resolve_start(conn)
        start_day = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).date()
        missing  = max(0, (int(time.time() * 1000) - start_ms) // DAY_MS)

        print(f"Symbol    : {SYMBOL}")
        print(f"Timeframe : {TIMEFRAME}")
        print(f"DB rows   : {before}")
        print(f"Missing   : ~{missing} days  (starting {start_day})")

        t0 = time.time()
        rows = fetch_all(start_ms)
        if not rows:
            print("No new candles to insert (already up to date).")
            return 0
        upsert(conn, rows)
        after = count_rows(conn)
        f = datetime.fromtimestamp(rows[0][0]  / 1000, tz=timezone.utc).date()
        l = datetime.fromtimestamp(rows[-1][0] / 1000, tz=timezone.utc).date()
        print(f"Done: {len(rows)} rows  {f} -> {l}  in {time.time()-t0:.1f}s")
        print(f"DB rows   : {before} -> {after}  (+{after-before})")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    update()

