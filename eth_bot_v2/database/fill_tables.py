"""
Fill every table in database/market.db with real or sample data.

Uses Binance public endpoints (no API key needed) for:
    ohlcv, funding_rate, open_interest, trades, orderbook,
    liquidations (approximate from forceOrder stream — mocked if unavailable),
    long_short_ratio is represented via open_interest if missing

Tables with no free public source get a tiny 1-2 row sample
so you can see the column shape:
    option_chain, greeks, implied_volatility, news, onchain, whales, fear_greed

Run:
    python database\\fill_tables.py
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

DB_PATH = Path(__file__).resolve().parent / "market.db"

FUTURES = "https://fapi.binance.com"
SPOT    = "https://api.binance.com"

SYMBOL    = "ETHUSDT"
DAY_MS    = 86_400_000
HOUR_MS   = 3_600_000
MIN_MS    = 60_000


# ---------- helpers ---------------------------------------------------------

def req(url, params=None, timeout=15):
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def count(conn, table) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def now_ms() -> int:
    return int(time.time() * 1000)


# ---------- fillers ---------------------------------------------------------

def fill_ohlcv(conn):
    """Already populated by the updater — top up if empty."""
    n = count(conn, "ohlcv")
    if n > 0:
        print(f"  ohlcv already has {n} rows, skipping")
        return
    print("  fetching ohlcv (last 1000 days)...")
    start = now_ms() - 1000 * DAY_MS
    rows = req(f"{SPOT}/api/v3/klines",
               {"symbol": SYMBOL, "interval": "1d", "startTime": start, "limit": 1000})
    conn.executemany(
        "INSERT OR IGNORE INTO ohlcv VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [(SYMBOL, "1d", int(k[0]), int(k[6]),
          float(k[1]), float(k[2]), float(k[3]), float(k[4]),
          float(k[5]), float(k[7]), int(k[8])) for k in rows])
    conn.commit()
    print(f"    +{len(rows)} rows")


def fill_funding_rate(conn):
    if count(conn, "funding_rate") > 0:
        print("  funding_rate already filled, skipping"); return
    print("  fetching funding_rate (last 1000 periods = ~333 days)...")
    rows = req(f"{FUTURES}/fapi/v1/fundingRate",
               {"symbol": SYMBOL, "limit": 1000})
    conn.executemany(
        "INSERT OR IGNORE INTO funding_rate VALUES (?,?,?)",
        [(SYMBOL, int(r["fundingTime"]), float(r["fundingRate"])) for r in rows])
    conn.commit()
    print(f"    +{len(rows)} rows")


def fill_open_interest(conn):
    if count(conn, "open_interest") > 0:
        print("  open_interest already filled, skipping"); return
    print("  fetching open_interest history (last 500 daily points)...")
    rows = req(f"{FUTURES}/futures/data/openInterestHist",
               {"symbol": SYMBOL, "period": "1d", "limit": 500})
    conn.executemany(
        "INSERT OR IGNORE INTO open_interest VALUES (?,?,?,?)",
        [(SYMBOL, int(r["timestamp"]),
          float(r["sumOpenInterest"]),
          float(r["sumOpenInterestValue"])) for r in rows])
    conn.commit()
    print(f"    +{len(rows)} rows")


def fill_trades(conn):
    if count(conn, "trades") > 0:
        print("  trades already filled, skipping"); return
    print("  fetching trades (last 1000 spot trades)...")
    rows = req(f"{SPOT}/api/v3/trades",
               {"symbol": SYMBOL, "limit": 1000})
    conn.executemany(
        "INSERT OR IGNORE INTO trades VALUES (?,?,?,?,?,?)",
        [(SYMBOL, int(r["id"]), int(r["time"]),
          float(r["price"]), float(r["qty"]),
          1 if r["isBuyerMaker"] else 0) for r in rows])
    conn.commit()
    print(f"    +{len(rows)} rows")


def fill_orderbook(conn):
    if count(conn, "orderbook") > 0:
        print("  orderbook already filled, skipping"); return
    print("  fetching orderbook snapshot (top 20 levels)...")
    ob = req(f"{SPOT}/api/v3/depth",
             {"symbol": SYMBOL, "limit": 20})
    ts = now_ms()
    bids = [(SYMBOL, ts - i, float(p), float(q), 0.0, 0.0) for i, (p, q) in enumerate(ob["bids"])]
    asks = [(SYMBOL, ts - i, 0.0, 0.0, float(p), float(q)) for i, (p, q) in enumerate(ob["asks"])]
    conn.executemany("INSERT OR IGNORE INTO orderbook VALUES (?,?,?,?,?,?)",
                     bids + asks)
    conn.commit()
    print(f"    +{len(bids)+len(asks)} rows")


def fill_liquidations(conn):
    if count(conn, "liquidations") > 0:
        print("  liquidations already filled, skipping"); return
    print("  liquidations: no historical public endpoint — inserting 3 sample rows")
    ts = now_ms()
    sample = [
        (SYMBOL, ts - 1 * HOUR_MS, "long",  2400.0, 1.5,  3600.0),
        (SYMBOL, ts - 2 * HOUR_MS, "short", 2450.0, 0.8,  1960.0),
        (SYMBOL, ts - 3 * HOUR_MS, "long",  2380.0, 2.1,  4998.0),
    ]
    conn.executemany("INSERT OR IGNORE INTO liquidations VALUES (?,?,?,?,?,?)", sample)
    conn.commit()
    print(f"    +{len(sample)} sample rows")


def fill_option_chain(conn):
    if count(conn, "option_chain") > 0:
        print("  option_chain already filled, skipping"); return
    print("  fetching Deribit ETH option chain...")
    try:
        data = req("https://www.deribit.com/api/v2/public/get_book_summary_by_currency",
                   {"currency": "ETH", "kind": "option"}, timeout=20)
        rows = []
        ts = now_ms()
        for r in data["result"][:200]:          # cap at 200
            name = r["instrument_name"]         # ETH-26DEC25-3000-C
            parts = name.split("-")
            if len(parts) != 4: continue
            _, expiry_str, strike_str, kind = parts
            try:
                expiry_dt = datetime.strptime(expiry_str, "%d%b%y").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            rows.append((
                "ETH",
                int(expiry_dt.timestamp() * 1000),
                float(strike_str),
                kind,
                ts,
                float(r.get("mark_price") or 0),
                float(r.get("bid_price") or 0),
                float(r.get("ask_price") or 0),
                float(r.get("mark_iv") or 0),
                float(r.get("open_interest") or 0),
                float(r.get("volume") or 0),
            ))
        conn.executemany("INSERT OR IGNORE INTO option_chain VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
        print(f"    +{len(rows)} rows")
    except Exception as e:
        print(f"    deribit failed ({e}), inserting 1 sample row")
        ts = now_ms()
        conn.execute("INSERT OR IGNORE INTO option_chain VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     ("ETH", ts + 30*DAY_MS, 3000.0, "C", ts,
                      120.0, 118.0, 122.0, 0.65, 1500.0, 42.0))
        conn.commit()


def fill_greeks(conn):
    if count(conn, "greeks") > 0:
        print("  greeks already filled, skipping"); return
    print("  greeks: computed from option_chain row count — inserting 1 sample row")
    ts = now_ms()
    conn.execute("INSERT OR IGNORE INTO greeks VALUES (?,?,?,?,?,?,?,?,?,?)",
                 ("ETH", ts + 30*DAY_MS, 3000.0, "C", ts,
                  0.52, 0.0012, -45.3, 12.8, 8.1))
    conn.commit()
    print("    +1 sample row")


def fill_implied_volatility(conn):
    if count(conn, "implied_volatility") > 0:
        print("  implied_volatility already filled, skipping"); return
    # derive from option_chain if possible
    rows = conn.execute(
        "SELECT underlying, expiry, strike, kind, ts, iv "
        "FROM option_chain WHERE iv > 0 LIMIT 500").fetchall()
    if rows:
        conn.executemany("INSERT OR IGNORE INTO implied_volatility VALUES (?,?,?,?,?,?)", rows)
        conn.commit()
        print(f"    +{len(rows)} rows (copied from option_chain.iv)")
    else:
        print("  implied_volatility: no source — inserting 1 sample row")
        ts = now_ms()
        conn.execute("INSERT OR IGNORE INTO implied_volatility VALUES (?,?,?,?,?,?)",
                     ("ETH", ts + 30*DAY_MS, 3000.0, "C", ts, 0.65))
        conn.commit()
        print("    +1 sample row")


def fill_news(conn):
    if count(conn, "news") > 0:
        print("  news already filled, skipping"); return
    print("  news: no key — inserting 2 sample rows")
    ts = now_ms()
    sample = [
        ("sample-1", ts - 1 * HOUR_MS, "coindesk",
         "Sample: ETH holds above $2400",
         "https://example.com/a", 0.12, "Sample body."),
        ("sample-2", ts - 3 * HOUR_MS, "theblock",
         "Sample: ETF inflows continue",
         "https://example.com/b", 0.34, "Sample body."),
    ]
    conn.executemany("INSERT OR IGNORE INTO news VALUES (?,?,?,?,?,?,?)", sample)
    conn.commit()
    print("    +2 sample rows")


def fill_onchain(conn):
    if count(conn, "onchain") > 0:
        print("  onchain already filled, skipping"); return
    print("  onchain: no key — inserting 3 sample metrics")
    ts = now_ms() // DAY_MS * DAY_MS       # today at 00:00 UTC
    sample = [
        ("active_addresses", ts, 512_000.0),
        ("gas_price_gwei",   ts, 14.3),
        ("eth_staked",       ts, 34_200_000.0),
    ]
    conn.executemany("INSERT OR IGNORE INTO onchain VALUES (?,?,?)", sample)
    conn.commit()
    print("    +3 sample rows")


def fill_whales(conn):
    if count(conn, "whales") > 0:
        print("  whales already filled, skipping"); return
    print("  whales: no key — inserting 2 sample rows")
    ts = now_ms()
    sample = [
        ("0xsamplehash1", ts - 30*MIN_MS, "0xabc", "0xdef", 12_500.0, "ETH"),
        ("0xsamplehash2", ts - 90*MIN_MS, "0x123", "0x456",  3_200.0, "ETH"),
    ]
    conn.executemany("INSERT OR IGNORE INTO whales VALUES (?,?,?,?,?,?)", sample)
    conn.commit()
    print("    +2 sample rows")


def fill_fear_greed(conn):
    if count(conn, "fear_greed") > 0:
        print("  fear_greed already filled, skipping"); return
    print("  fetching fear_greed (alternative.me)...")
    try:
        data = req("https://api.alternative.me/fng/",
                   {"limit": 2000, "format": "json"}, timeout=20)
        rows = []
        for r in data["data"]:
            ts = int(r["timestamp"]) * 1000
            rows.append((ts, int(r["value"]), r["value_classification"]))
        conn.executemany("INSERT OR IGNORE INTO fear_greed VALUES (?,?,?)", rows)
        conn.commit()
        print(f"    +{len(rows)} rows")
    except Exception as e:
        print(f"    failed ({e}), inserting 1 sample row")
        conn.execute("INSERT OR IGNORE INTO fear_greed VALUES (?,?,?)",
                     (now_ms() // DAY_MS * DAY_MS, 55, "Greed"))
        conn.commit()


# ---------- main ------------------------------------------------------------

FILLERS = [
    ("ohlcv",               fill_ohlcv),
    ("orderbook",           fill_orderbook),
    ("trades",              fill_trades),
    ("open_interest",       fill_open_interest),
    ("funding_rate",        fill_funding_rate),
    ("option_chain",        fill_option_chain),
    ("greeks",              fill_greeks),
    ("implied_volatility",  fill_implied_volatility),
    ("liquidations",        fill_liquidations),
    ("news",                fill_news),
    ("onchain",             fill_onchain),
    ("whales",              fill_whales),
    ("fear_greed",          fill_fear_greed),
]


def main() -> int:
    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        print("Run: python database\\init_db.py")
        return 1

    conn = sqlite3.connect(DB_PATH)
    try:
        print(f"DB: {DB_PATH}\n")
        for name, fn in FILLERS:
            print(f"[{name}]")
            try:
                fn(conn)
            except Exception as e:
                print(f"  ERROR: {e}")
            print()

        print("=" * 60)
        print("Final row counts:")
        for t, _ in FILLERS:
            print(f"  {t:<22} rows={count(conn, t)}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())