"""Fetch ALL ETH/BTC options data from Deribit into options.db.

Fetches:
  - book summary (chain snapshot, all instruments)
  - ticker for each instrument (includes greeks)
  - aggregates into option_summary

Stores date column on every row.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "options.db"
DERIBIT = "https://www.deribit.com/api/v2"


def req(path, params=None, timeout=20):
    r = requests.get(f"{DERIBIT}{path}", params=params or {}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result", data)


def now():
    ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return ts, dt


def parse_instrument(name):
    parts = name.split("-")
    if len(parts) != 4:
        return None
    underlying, expiry_str, strike_str, kind = parts
    try:
        expiry_dt = datetime.strptime(expiry_str, "%d%b%y").replace(tzinfo=timezone.utc)
        strike = float(strike_str)
    except ValueError:
        return None
    return {
        "underlying": underlying,
        "expiry":     int(expiry_dt.timestamp() * 1000),
        "strike":     strike,
        "kind":       kind,
    }


def insert_chain(conn, ts, date_str, rows):
    conn.executemany(
        """INSERT OR REPLACE INTO option_chain
           (underlying, expiry, strike, kind, ts, date,
            mark_price, bid, ask, bid_iv, ask_iv, mark_iv,
            oi, volume, underlying_px)
           VALUES (?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?)""",
        rows)
    conn.commit()


def insert_greeks(conn, ts, date_str, rows):
    conn.executemany(
        """INSERT OR REPLACE INTO greeks
           (underlying, expiry, strike, kind, ts, date,
            delta, gamma, theta, vega, rho)
           VALUES (?,?,?,?,?,?, ?,?,?,?,?)""",
        rows)
    conn.commit()


def insert_iv(conn, ts, date_str, rows):
    conn.executemany(
        """INSERT OR REPLACE INTO implied_volatility
           (underlying, expiry, strike, kind, ts, date,
            iv, iv_fit, moneyness, dte)
           VALUES (?,?,?,?,?,?, ?,?,?,?)""",
        rows)
    conn.commit()


def insert_summary(conn, row):
    conn.execute(
        """INSERT OR REPLACE INTO option_summary
           (underlying, ts, date,
            total_oi_call, total_oi_put, pcr_oi,
            total_vol_call, total_vol_put, pcr_vol,
            atm_iv, iv_25d_skew, term_structure, max_pain,
            n_instruments, underlying_px,
            put_oi_max_strike, call_oi_max_strike)
           VALUES (?,?,?, ?,?,?, ?,?,?, ?,?,?,?, ?,?, ?,?)""",
        row)
    conn.commit()


def compute_summary(currency, ts, date_str, snapshot):
    """Full aggregate - all the numbers we can derive."""
    total_oi_call = total_oi_put = 0.0
    total_vol_call = total_vol_put = 0.0
    oi_by_strike = {}
    put_oi_by_strike = {}
    call_oi_by_strike = {}
    underlying_px = None
    n = 0

    for s in snapshot:
        info = parse_instrument(s.get("instrument_name", ""))
        if not info:
            continue
        n += 1

        oi = float(s.get("open_interest") or 0)
        vol = float(s.get("volume") or 0)

        if info["kind"] == "C":
            total_oi_call += oi
            total_vol_call += vol
            call_oi_by_strike[info["strike"]] = call_oi_by_strike.get(info["strike"], 0) + oi
        else:
            total_oi_put += oi
            total_vol_put += vol
            put_oi_by_strike[info["strike"]] = put_oi_by_strike.get(info["strike"], 0) + oi

        oi_by_strike[info["strike"]] = oi_by_strike.get(info["strike"], 0) + oi

        if underlying_px is None and s.get("underlying_price"):
            underlying_px = float(s["underlying_price"])

    pcr_oi  = (total_oi_put / total_oi_call) if total_oi_call else None
    pcr_vol = (total_vol_put / total_vol_call) if total_vol_call else None
    max_pain = max(oi_by_strike, key=oi_by_strike.get) if oi_by_strike else None
    put_max = max(put_oi_by_strike, key=put_oi_by_strike.get) if put_oi_by_strike else None
    call_max = max(call_oi_by_strike, key=call_oi_by_strike.get) if call_oi_by_strike else None

    return (currency, ts, date_str,
            total_oi_call, total_oi_put, pcr_oi,
            total_vol_call, total_vol_put, pcr_vol,
            None, None, None, max_pain,
            n, underlying_px,
            put_max, call_max)


def fetch_currency(conn, currency, fetch_greeks=False):
    ts, date_str = now()
    print(f"[{currency}]  {date_str} UTC")

    try:
        snapshot = req("/public/get_book_summary_by_currency",
                       {"currency": currency, "kind": "option"})
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        return 0

    if not snapshot:
        print("  no instruments")
        return 0

    print(f"  {len(snapshot)} instruments in book summary")

    chain_rows = []
    greeks_rows = []
    iv_rows = []

    for s in snapshot:
        info = parse_instrument(s.get("instrument_name", ""))
        if not info:
            continue

        underlying_px = s.get("underlying_price")
        underlying_px = float(underlying_px) if underlying_px else None

        mark_iv = s.get("mark_iv")
        mark_iv = float(mark_iv) / 100.0 if mark_iv is not None else None
        bid_iv  = s.get("bid_iv")
        bid_iv  = float(bid_iv) / 100.0 if bid_iv is not None else None
        ask_iv  = s.get("ask_iv")
        ask_iv  = float(ask_iv) / 100.0 if ask_iv is not None else None

        chain_rows.append((
            info["underlying"], info["expiry"], info["strike"], info["kind"],
            ts, date_str,
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
                info["underlying"], info["expiry"], info["strike"], info["kind"],
                ts, date_str,
                mark_iv, None, moneyness, dte,
            ))

    insert_chain(conn, ts, date_str, chain_rows)
    print(f"  option_chain          +{len(chain_rows)} rows")

    if iv_rows:
        insert_iv(conn, ts, date_str, iv_rows)
        print(f"  implied_volatility    +{len(iv_rows)} rows")

    # optional: fetch greeks per instrument (slow - 1 call per instrument)
    if fetch_greeks:
        print(f"  fetching greeks ({len(snapshot)} calls, slow)...")
        for i, s in enumerate(snapshot):
            info = parse_instrument(s.get("instrument_name", ""))
            if not info:
                continue
            try:
                tick = req("/public/ticker",
                           {"instrument_name": s["instrument_name"]})
                g = tick.get("greeks", {})
                greeks_rows.append((
                    info["underlying"], info["expiry"], info["strike"], info["kind"],
                    ts, date_str,
                    g.get("delta"), g.get("gamma"), g.get("theta"),
                    g.get("vega"),  g.get("rho"),
                ))
                if (i + 1) % 50 == 0:
                    print(f"    {i+1}/{len(snapshot)}")
                time.sleep(0.05)
            except Exception as e:
                pass

        if greeks_rows:
            insert_greeks(conn, ts, date_str, greeks_rows)
            print(f"  greeks                +{len(greeks_rows)} rows")

    summary = compute_summary(currency, ts, date_str, snapshot)
    insert_summary(conn, summary)
    print(f"  option_summary        +1 row")
    print(f"    date          = {date_str}")
    print(f"    pcr_oi        = {summary[5]}")
    print(f"    max_pain      = {summary[12]}")
    print(f"    put_oi_max    = {summary[15]}")
    print(f"    call_oi_max   = {summary[16]}")
    print(f"    underlying_px = {summary[14]}")

    return len(chain_rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--currency", type=str, default="ETH")
    ap.add_argument("--greeks", action="store_true",
                    help="also fetch greeks per instrument (slow)")
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
    print(f"  greeks    : {'yes' if args.greeks else 'no'}")
    print()

    conn = sqlite3.connect(DB_PATH)
    try:
        for cur in currencies:
            try:
                fetch_currency(conn, cur, fetch_greeks=args.greeks)
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