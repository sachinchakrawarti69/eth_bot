"""Fetch ETH/BTC options data from Deribit into options.db.

Usage:
    python -m scripts_python.fetchers.options
    python -m scripts_python.fetchers.options --currency ETH
    python -m scripts_python.fetchers.options --currency ETH,BTC
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "options.db"

DERIBIT = "https://www.deribit.com/api/v2"


def req(path: str, params: dict | None = None) -> dict:
    url = f"{DERIBIT}{path}"
    r = requests.get(url, params=params or {}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result", data)


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def parse_instrument(name: str):
    parts = name.split("-")
    if len(parts) != 4:
        return None
    underlying, expiry_str, strike_str, kind = parts
    try:
        expiry_dt = datetime.strptime(expiry_str, "%d%b%y").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    try:
        strike = float(strike_str)
    except ValueError:
        return None
    return {
        "underlying": underlying,
        "expiry":     int(expiry_dt.timestamp() * 1000),
        "strike":     strike,
        "kind":       kind,
    }


def upsert_chain(conn, ts, rows):
    conn.executemany(
        """INSERT INTO option_chain
           (underlying, expiry, strike, kind, ts,
            mark_price, bid, ask, bid_iv, ask_iv, mark_iv,
            oi, volume, underlying_px)
           VALUES (?,?,?,?,?, ?,?,?,?,?,?, ?,?,?)
           ON CONFLICT(underlying, expiry, strike, kind, ts) DO UPDATE SET
             mark_price=excluded.mark_price, bid=excluded.bid, ask=excluded.ask,
             bid_iv=excluded.bid_iv, ask_iv=excluded.ask_iv,
             mark_iv=excluded.mark_iv, oi=excluded.oi,
             volume=excluded.volume, underlying_px=excluded.underlying_px""",
        rows)
    conn.commit()


def upsert_iv(conn, ts, rows):
    conn.executemany(
        """INSERT INTO implied_volatility
           (underlying, expiry, strike, kind, ts, iv, iv_fit, moneyness, dte)
           VALUES (?,?,?,?,?, ?,?,?,?)
           ON CONFLICT(underlying, expiry, strike, kind, ts) DO UPDATE SET
             iv=excluded.iv, iv_fit=excluded.iv_fit,
             moneyness=excluded.moneyness, dte=excluded.dte""",
        rows)
    conn.commit()


def upsert_summary(conn, row):
    conn.execute(
        """INSERT INTO option_summary
           (underlying, ts, total_oi_call, total_oi_put, pcr_oi,
            total_vol_call, total_vol_put, pcr_vol,
            atm_iv, iv_25d_skew, term_structure, max_pain)
           VALUES (?,?,?,?,?, ?,?,?, ?,?,?,?)
           ON CONFLICT(underlying, ts) DO UPDATE SET
             total_oi_call=excluded.total_oi_call,
             total_oi_put=excluded.total_oi_put,
             pcr_oi=excluded.pcr_oi,
             total_vol_call=excluded.total_vol_call,
             total_vol_put=excluded.total_vol_put,
             pcr_vol=excluded.pcr_vol,
             atm_iv=excluded.atm_iv,
             iv_25d_skew=excluded.iv_25d_skew,
             term_structure=excluded.term_structure,
             max_pain=excluded.max_pain""",
        row)
    conn.commit()


def compute_summary(underlying, ts, snapshot):
    total_oi_call = total_oi_put = 0.0
    total_vol_call = total_vol_put = 0.0
    oi_by_strike = {}

    for s in snapshot:
        info = parse_instrument(s.get("instrument_name", ""))
        if not info:
            continue

        oi = float(s.get("open_interest") or 0)
        vol = float(s.get("volume") or 0)

        if info["kind"] == "C":
            total_oi_call += oi
            total_vol_call += vol
        else:
            total_oi_put += oi
            total_vol_put += vol

        oi_by_strike[info["strike"]] = oi_by_strike.get(info["strike"], 0) + oi

    pcr_oi  = (total_oi_put / total_oi_call) if total_oi_call else None
    pcr_vol = (total_vol_put / total_vol_call) if total_vol_call else None
    max_pain = max(oi_by_strike, key=oi_by_strike.get) if oi_by_strike else None

    return (underlying, ts,
            total_oi_call, total_oi_put, pcr_oi,
            total_vol_call, total_vol_put, pcr_vol,
            None, None, None, max_pain)


def fetch_currency(conn, currency):
    print(f"[{currency}]")
    print(f"  calling Deribit...")

    try:
        snapshot = req("/public/get_book_summary_by_currency",
                       {"currency": currency, "kind": "option"})
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        return 0

    if not snapshot:
        print(f"  no instruments returned")
        return 0

    print(f"  {len(snapshot)} instruments")
    ts = now_ms()

    chain_rows = []
    iv_rows = []

    for s in snapshot:
        info = parse_instrument(s.get("instrument_name", ""))
        if not info:
            continue

        underlying_px = s.get("underlying_price")
        underlying_px = float(underlying_px) if underlying_px else None

        mark_iv = s.get("mark_iv")
        mark_iv = float(mark_iv) / 100.0 if mark_iv is not None else None
        bid_iv = s.get("bid_iv")
        bid_iv = float(bid_iv) / 100.0 if bid_iv is not None else None
        ask_iv = s.get("ask_iv")
        ask_iv = float(ask_iv) / 100.0 if ask_iv is not None else None

        chain_rows.append((
            info["underlying"], info["expiry"], info["strike"], info["kind"], ts,
            float(s.get("mark_price") or 0),
            float(s.get("bid_price") or 0),
            float(s.get("ask_price") or 0),
            bid_iv, ask_iv, mark_iv,
            float(s.get("open_interest") or 0),
            float(s.get("volume") or 0),
            underlying_px,
        ))

        moneyness = info["strike"] / underlying_px if underlying_px else None
        dte = (info["expiry"] - ts) / 86_400_000.0 if info["expiry"] else None

        if mark_iv is not None:
            iv_rows.append((
                info["underlying"], info["expiry"], info["strike"], info["kind"], ts,
                mark_iv, None, moneyness, dte,
            ))

    upsert_chain(conn, ts, chain_rows)
    print(f"  option_chain          +{len(chain_rows)} rows")

    if iv_rows:
        upsert_iv(conn, ts, iv_rows)
        print(f"  implied_volatility    +{len(iv_rows)} rows")

    summary = compute_summary(currency, ts, snapshot)
    upsert_summary(conn, summary)
    print(f"  option_summary        +1 row")
    print(f"    pcr_oi   = {summary[4]}")
    print(f"    max_pain = {summary[11]}")

    return len(chain_rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--currency", type=str, default="ETH")
    args = ap.parse_args()
    currencies = [c.strip().upper() for c in args.currency.split(",") if c.strip()]

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        print("Run: python database/init_options_db.py")
        return 1

    print("=" * 60)
    print("  FETCH OPTIONS  ->  options.db")
    print("=" * 60)
    print(f"  currencies: {', '.join(currencies)}")
    print()

    conn = sqlite3.connect(DB_PATH)
    try:
        for cur in currencies:
            try:
                fetch_currency(conn, cur)
            except Exception as e:
                print(f"  {cur} FAIL: {type(e).__name__}: {e}")
            print()

        print("=" * 60)
        print("  TABLE COUNTS  (options.db)")
        print("=" * 60)
        for t in ("option_chain", "greeks", "implied_volatility", "option_summary"):
            try:
                n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"  {t:<22} {n:>7}")
            except Exception as e:
                print(f"  {t:<22} ERROR: {e}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
