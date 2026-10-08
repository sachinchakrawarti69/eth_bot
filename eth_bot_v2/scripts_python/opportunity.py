"""Generate today's trade setups.

Runs the winning backtest strategies against the current market
state. Produces conditional entry orders with window, trigger,
entry, stop, target.

Usage:
    python -m scripts_python.opportunity
    python -m scripts_python.opportunity --account 1000 --risk 1.0
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"
OUT_DIR = ROOT / "reports" / "orders"


# which strategies to run (from Phase 5 winners)
ACTIVE_STRATEGIES = [
    "rsi_oversold",
    "bull_dip",
    "bull_dip_st",
    "mean_reversion",
    "fade_longs",
    "fade_funding",
]


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------

def load_latest_features(conn, symbol):
    """Latest row + last 200 rows for context."""
    df = pd.read_sql_query(
        "SELECT * FROM features WHERE symbol=? ORDER BY ts DESC LIMIT 200",
        conn, params=(symbol,))
    if df.empty:
        return None, None
    df = df.sort_values("ts").reset_index(drop=True)
    return df, df.iloc[-1]


def load_btc_features(conn):
    df = pd.read_sql_query(
        "SELECT * FROM features WHERE symbol='BTCUSDT' ORDER BY ts DESC LIMIT 200",
        conn)
    if df.empty:
        return None
    return df.sort_values("ts").reset_index(drop=True)


def find_nearest_sr(conn, symbol, price, kind):
    """Find nearest S/R level above/below current price."""
    try:
        df = pd.read_sql_query(
            """SELECT level, kind, strength FROM sr_levels
               WHERE symbol=? AND timeframe='1h'
                 AND ts = (SELECT MAX(ts) FROM sr_levels WHERE symbol=?)
               ORDER BY level""",
            conn, params=(symbol, symbol))
    except Exception:
        return None, None
    if df.empty:
        return None, None

    if kind == "support":
        below = df[(df["kind"] == "support") & (df["level"] < price)]
        if not below.empty:
            r = below.iloc[-1]
            return float(r["level"]), float(r["strength"])
    else:
        above = df[(df["kind"] == "resistance") & (df["level"] > price)]
        if not above.empty:
            r = above.iloc[0]
            return float(r["level"]), float(r["strength"])

    return None, None


# ------------------------------------------------------------------
# strategy rules (entry conditions + exit plan)
# ------------------------------------------------------------------

def make_setup_rsi_oversold(conn, symbol, last, price, atr):
    """Buy when 1h RSI < 25. Hold 12h. Stop 1.5 ATR, target 2x."""
    if not (last["rsi_14"] < 25):
        return None

    stop_dist = 1.5 * atr
    entry = price
    stop = entry - stop_dist
    target = entry + 2 * stop_dist

    return {
        "direction": "LONG",
        "trigger": f"price <= {entry:.2f}",
        "trigger_price": entry,
        "entry": entry,
        "stop": stop,
        "target": target,
        "hold_hours": 12,
    }


def make_setup_bull_dip(conn, symbol, last, price, atr):
    """Buy when regime bull AND RSI 1h < 30. Hold 24h."""
    if not (last["regime"] == "bull" and last["rsi_14"] < 30):
        return None

    stop_dist = 1.5 * atr
    entry = price
    stop = entry - stop_dist
    target = entry + 2 * stop_dist

    return {
        "direction": "LONG",
        "trigger": f"price <= {entry:.2f}",
        "trigger_price": entry,
        "entry": entry,
        "stop": stop,
        "target": target,
        "hold_hours": 24,
    }


def make_setup_bull_dip_st(conn, symbol, last, price, atr):
    """Same as bull_dip but with 2% stop / 4% target."""
    if not (last["regime"] == "bull" and last["rsi_14"] < 30):
        return None

    entry = price
    stop = entry * 0.98
    target = entry * 1.04

    return {
        "direction": "LONG",
        "trigger": f"price <= {entry:.2f}",
        "trigger_price": entry,
        "entry": entry,
        "stop": stop,
        "target": target,
        "hold_hours": 24,
    }


def make_setup_mean_reversion(conn, symbol, last, price, atr):
    """Buy when 4h RSI < 30. Hold 24h."""
    if not (last["rsi_14_4h"] < 30):
        return None

    stop_dist = 1.5 * atr
    entry = price
    stop = entry - stop_dist
    target = entry + 2 * stop_dist

    return {
        "direction": "LONG",
        "trigger": f"price <= {entry:.2f}",
        "trigger_price": entry,
        "entry": entry,
        "stop": stop,
        "target": target,
        "hold_hours": 24,
    }


def make_setup_fade_longs(conn, symbol, last, price, atr):
    """Short when ls_ratio > 1.5. Hold 24h."""
    if pd.isna(last.get("ls_ratio")) or not (last["ls_ratio"] > 1.5):
        return None

    stop_dist = 1.5 * atr
    entry = price
    stop = entry + stop_dist
    target = entry - 2 * stop_dist

    return {
        "direction": "SHORT",
        "trigger": f"price >= {entry:.2f}",
        "trigger_price": entry,
        "entry": entry,
        "stop": stop,
        "target": target,
        "hold_hours": 24,
    }


def make_setup_fade_funding(conn, symbol, last, price, atr):
    """Short when funding > 0.05%."""
    if pd.isna(last.get("funding")) or not (last["funding"] > 0.0005):
        return None

    stop_dist = 1.5 * atr
    entry = price
    stop = entry + stop_dist
    target = entry - 2 * stop_dist

    return {
        "direction": "SHORT",
        "trigger": f"price >= {entry:.2f}",
        "trigger_price": entry,
        "entry": entry,
        "stop": stop,
        "target": target,
        "hold_hours": 24,
    }


STRATEGY_BUILDERS = {
    "rsi_oversold":  make_setup_rsi_oversold,
    "bull_dip":      make_setup_bull_dip,
    "bull_dip_st":   make_setup_bull_dip_st,
    "mean_reversion":make_setup_mean_reversion,
    "fade_longs":    make_setup_fade_longs,
    "fade_funding":  make_setup_fade_funding,
}


# ------------------------------------------------------------------
# time window
# ------------------------------------------------------------------

def compute_window(now_utc, hold_hours):
    """Decide the trading window for a setup."""
    # if after 18:00 UTC and before 21:00 UTC, use rest of window
    h = now_utc.hour
    if 18 <= h < 21:
        start = now_utc
        end = now_utc.replace(hour=21, minute=0, second=0, microsecond=0)
    else:
        # next 18:00 UTC
        start = (now_utc + timedelta(days=1)).replace(
            hour=18, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=3)
    return start, end


# ------------------------------------------------------------------
# position sizing
# ------------------------------------------------------------------

def compute_size(account, risk_pct, entry, stop):
    risk_usd = account * risk_pct / 100
    stop_dist = abs(entry - stop)
    if stop_dist <= 0:
        return 0.0, risk_usd
    units = risk_usd / stop_dist
    return units, risk_usd


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def generate_setups(conn, symbols, account, risk_pct, now_utc):
    setups = []
    date_str = now_utc.strftime("%Y-%m-%d")

    for symbol in symbols:
        df, last = load_latest_features(conn, symbol)
        if last is None:
            continue

        price = float(last["close"])
        atr = float(last["atr_14"]) if pd.notna(last["atr_14"]) else price * 0.02

        # try each strategy
        for strat_name in ACTIVE_STRATEGIES:
            builder = STRATEGY_BUILDERS.get(strat_name)
            if builder is None:
                continue
            try:
                raw = builder(conn, symbol, last, price, atr)
            except Exception as e:
                print(f"  {symbol} {strat_name}: {e}")
                continue

            if raw is None:
                continue

            entry = raw["entry"]
            stop = raw["stop"]
            target = raw["target"]
            rr = abs(target - entry) / abs(entry - stop) if entry != stop else 0

            units, risk_usd = compute_size(account, risk_pct, entry, stop)

            win_start, win_end = compute_window(now_utc, raw["hold_hours"])

            # confidence: rough score
            conf = 0.5
            if last["regime"] == "bull" and raw["direction"] == "LONG":
                conf += 0.1
            if not pd.isna(last.get("rsi_14")) and last["rsi_14"] < 25:
                conf += 0.1
            if not pd.isna(last.get("rsi_14_4h")) and last["rsi_14_4h"] < 25:
                conf += 0.05

            setup = {
                "date": date_str,
                "symbol": symbol,
                "strategy": strat_name,
                "direction": raw["direction"],
                "created_ts": int(now_utc.timestamp() * 1000),
                "current_price": price,

                "entry": round(entry, 4),
                "stop": round(stop, 4),
                "target": round(target, 4),
                "rr": round(rr, 2),

                "size_units": round(units, 6),
                "risk_usd": round(risk_usd, 2),
                "account_usd": account,
                "risk_pct": risk_pct,

                "trigger_text": raw["trigger"],
                "trigger_price": round(raw["trigger_price"], 4),

                "window_start_ts": int(win_start.timestamp() * 1000),
                "window_end_ts":   int(win_end.timestamp() * 1000),
                "expiry_ts":       int((win_end + timedelta(hours=raw["hold_hours"])).timestamp() * 1000),

                "confidence": round(conf, 2),

                "invalidation": [
                    "BTC drops > 1.5% in 1h" if raw["direction"] == "LONG" else "BTC rises > 1.5% in 1h",
                    f"price breaks {'below' if raw['direction']=='LONG' else 'above'} {stop:.2f}",
                    f"window expires",
                ],
            }
            setups.append(setup)
    return setups


def save_setups(conn, setups):
    for s in setups:
        conn.execute(
            """INSERT OR REPLACE INTO trade_setups
               (date, symbol, strategy, direction, created_ts, current_price,
                entry, stop, target, rr, size_units, risk_usd, account_usd,
                risk_pct, trigger_text, trigger_price,
                window_start_ts, window_end_ts, expiry_ts,
                confidence, status)
               VALUES (?,?,?,?,?,?, ?,?,?,?,?,?,?, ?,?,?, ?,?,?, ?, ?)""",
            (s["date"], s["symbol"], s["strategy"], s["direction"],
             s["created_ts"], s["current_price"],
             s["entry"], s["stop"], s["target"], s["rr"],
             s["size_units"], s["risk_usd"], s["account_usd"], s["risk_pct"],
             s["trigger_text"], s["trigger_price"],
             s["window_start_ts"], s["window_end_ts"], s["expiry_ts"],
             s["confidence"], "pending"))
    conn.commit()


def print_setup(s):
    arrow = "LONG " if s["direction"] == "LONG" else "SHORT"
    print()
    print("=" * 66)
    print(f"  {arrow}  {s['symbol']}  via {s['strategy']}  (confidence {s['confidence']:.2f})")
    print("=" * 66)
    print(f"  current price : {s['current_price']:>12,.2f}")
    print(f"  trigger       : {s['trigger_text']}")
    print(f"  entry         : {s['entry']:>12,.2f}")
    print(f"  stop          : {s['stop']:>12,.2f}")
    print(f"  target        : {s['target']:>12,.2f}")
    print(f"  R:R           : {s['rr']:>12.2f}")
    print(f"  size          : {s['size_units']:>12.6f} units")
    print(f"  risk          : ${s['risk_usd']:.2f}  ({s['risk_pct']}% of ${s['account_usd']:.0f})")

    ws = datetime.fromtimestamp(s["window_start_ts"] / 1000, tz=timezone.utc)
    we = datetime.fromtimestamp(s["window_end_ts"] / 1000, tz=timezone.utc)
    print(f"  window        : {ws.strftime('%Y-%m-%d %H:%M UTC')} -> {we.strftime('%H:%M UTC')}")
    print("  invalidation:")
    for r in s["invalidation"]:
        print(f"    - {r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=str, default="BTCUSDT,ETHUSDT")
    ap.add_argument("--account", type=float, default=1000.0)
    ap.add_argument("--risk", type=float, default=1.0)
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    now = datetime.now(timezone.utc)

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='trade_setups'"
        ).fetchone()
        if not exists:
            print("trade_setups table not found - run: python database/init_db.py")
            return 1

        print("=" * 66)
        print("  OPPORTUNITY SCANNER")
        print("=" * 66)
        print(f"  time    : {now.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  symbols : {', '.join(symbols)}")
        print(f"  account : ${args.account:.2f}")
        print(f"  risk    : {args.risk}%")

        setups = generate_setups(conn, symbols, args.account, args.risk, now)

        if not setups:
            print()
            print("  no setups today")
            return 0

        print()
        print(f"  found {len(setups)} setups")

        for s in setups:
            print_setup(s)

        save_setups(conn, setups)
        print()
        print("=" * 66)
        print(f"  saved {len(setups)} setups to trade_setups")
        print("=" * 66)

        # also write JSON for the day
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"{now.strftime('%Y-%m-%d')}.json"
        path.write_text(json.dumps({
            "date": now.strftime("%Y-%m-%d"),
            "generated_at": now.isoformat(),
            "setups": setups,
        }, indent=2, default=str), encoding="utf-8")
        print(f"  wrote {path}")

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
