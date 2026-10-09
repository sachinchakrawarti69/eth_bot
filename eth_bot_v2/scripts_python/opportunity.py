"""Generate today's trade setups. One direction per symbol.

Collects all candidate signals, then picks the side with more votes.
If tie -> skip that symbol.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"
OUT_DIR = ROOT / "reports" / "orders"

ACTIVE_STRATEGIES = [
    "rsi_oversold", "bull_dip", "bull_dip_st",
    "mean_reversion", "fade_longs", "fade_funding",
]


def load_latest_features(conn, symbol):
    df = pd.read_sql_query(
        "SELECT * FROM features WHERE symbol=? ORDER BY ts DESC LIMIT 200",
        conn, params=(symbol,))
    if df.empty:
        return None, None
    df = df.sort_values("ts").reset_index(drop=True)
    return df, df.iloc[-1]


def compute_window(now_utc, hold_hours=24):
    h = now_utc.hour
    if 18 <= h < 21:
        start = now_utc
        end = now_utc.replace(hour=21, minute=0, second=0, microsecond=0)
    else:
        start = (now_utc + timedelta(days=1)).replace(
            hour=18, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=3)
    return start, end


def compute_size(account, risk_pct, entry, stop):
    risk_usd = account * risk_pct / 100
    d = abs(entry - stop)
    return (risk_usd / d if d > 0 else 0.0), risk_usd


def _mk(last, price, atr, direction, stop_mult=1.5, target_mult=2.0, hold=24):
    d = stop_mult * atr
    if direction == "LONG":
        return {"direction": "LONG", "entry": price,
                "stop": price - d, "target": price + target_mult * d,
                "hold": hold}
    return {"direction": "SHORT", "entry": price,
            "stop": price + d, "target": price - target_mult * d,
            "hold": hold}


def make_setup_rsi_oversold(conn, symbol, last, price, atr):
    if last["rsi_14"] >= 25: return None
    return _mk(last, price, atr, "LONG", hold=12)


def make_setup_bull_dip(conn, symbol, last, price, atr):
    if not (last["regime"] == "bull" and last["rsi_14"] < 30): return None
    return _mk(last, price, atr, "LONG")


def make_setup_bull_dip_st(conn, symbol, last, price, atr):
    if not (last["regime"] == "bull" and last["rsi_14"] < 30): return None
    return {"direction": "LONG", "entry": price,
            "stop": price * 0.98, "target": price * 1.04, "hold": 24}


def make_setup_mean_reversion(conn, symbol, last, price, atr):
    if last["rsi_14_4h"] >= 30: return None
    return _mk(last, price, atr, "LONG")


def make_setup_fade_longs(conn, symbol, last, price, atr):
    if pd.isna(last.get("ls_ratio")) or last["ls_ratio"] <= 1.5: return None
    return _mk(last, price, atr, "SHORT")


def make_setup_fade_funding(conn, symbol, last, price, atr):
    if pd.isna(last.get("funding")) or last["funding"] <= 0.0005: return None
    return _mk(last, price, atr, "SHORT")


BUILDERS = {
    "rsi_oversold":   make_setup_rsi_oversold,
    "bull_dip":       make_setup_bull_dip,
    "bull_dip_st":    make_setup_bull_dip_st,
    "mean_reversion": make_setup_mean_reversion,
    "fade_longs":     make_setup_fade_longs,
    "fade_funding":   make_setup_fade_funding,
}


def generate_setups(conn, symbols, account, risk_pct, now_utc):
    out = []
    date_str = now_utc.strftime("%Y-%m-%d")

    for sym in symbols:
        _, last = load_latest_features(conn, sym)
        if last is None:
            continue
        price = float(last["close"])
        atr = float(last["atr_14"]) if pd.notna(last["atr_14"]) else price * 0.02

        # collect all candidates
        candidates = []
        for name in ACTIVE_STRATEGIES:
            b = BUILDERS.get(name)
            if b is None:
                continue
            try:
                raw = b(conn, sym, last, price, atr)
            except Exception:
                continue
            if raw is None:
                continue

            entry = raw["entry"]
            stop = raw["stop"]
            target = raw["target"]
            rr = abs(target - entry) / abs(entry - stop) if entry != stop else 0
            units, risk_usd = compute_size(account, risk_pct, entry, stop)
            ws, we = compute_window(now_utc, raw["hold"])

            conf = 0.5
            if last["regime"] == "bull" and raw["direction"] == "LONG":
                conf += 0.1
            if pd.notna(last.get("rsi_14")) and last["rsi_14"] < 25:
                conf += 0.1

            candidates.append({
                "strategy":   name,
                "direction":  raw["direction"],
                "entry":      entry,
                "stop":       stop,
                "target":     target,
                "rr":         rr,
                "units":      units,
                "risk_usd":   risk_usd,
                "ws":         ws,
                "we":         we,
                "hold":       raw["hold"],
                "confidence": conf,
            })

        if not candidates:
            continue

        longs = [c for c in candidates if c["direction"] == "LONG"]
        shorts = [c for c in candidates if c["direction"] == "SHORT"]

        if len(longs) > len(shorts):
            winner = max(longs, key=lambda x: x["confidence"])
        elif len(shorts) > len(longs):
            winner = max(shorts, key=lambda x: x["confidence"])
        else:
            continue   # tie -> no setup

        trig = "<=" if winner["direction"] == "LONG" else ">="
        out.append({
            "date":          date_str,
            "symbol":        sym,
            "strategy":      winner["strategy"],
            "direction":     winner["direction"],
            "created_ts":    int(now_utc.timestamp() * 1000),
            "current_price": price,
            "entry":         round(winner["entry"], 4),
            "stop":          round(winner["stop"], 4),
            "target":        round(winner["target"], 4),
            "rr":            round(winner["rr"], 2),
            "size_units":    round(winner["units"], 6),
            "risk_usd":      round(winner["risk_usd"], 2),
            "account_usd":   account,
            "risk_pct":      risk_pct,
            "trigger_text":  "price " + trig + " " + format(winner["entry"], ".2f"),
            "trigger_price": round(winner["entry"], 4),
            "window_start_ts": int(winner["ws"].timestamp() * 1000),
            "window_end_ts":   int(winner["we"].timestamp() * 1000),
            "expiry_ts":       int((winner["we"] + timedelta(hours=winner["hold"])).timestamp() * 1000),
            "confidence":      round(winner["confidence"], 2),
            "votes_long":      len(longs),
            "votes_short":     len(shorts),
        })

    return out


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
    print("  " + arrow + "  " + s["symbol"] + "  via " + s["strategy"] +
          "  (conf " + format(s["confidence"], ".2f") + ")")
    print("=" * 66)
    print("  current       : " + format(s["current_price"], ">12,.2f"))
    print("  trigger       : " + s["trigger_text"])
    print("  entry         : " + format(s["entry"], ">12,.2f"))
    print("  stop          : " + format(s["stop"], ">12,.2f"))
    print("  target        : " + format(s["target"], ">12,.2f"))
    print("  R:R           : " + format(s["rr"], ">12.2f"))
    print("  size          : " + format(s["size_units"], ">12.6f") + " units")
    print("  risk          : $" + format(s["risk_usd"], ".2f") +
          "  (" + str(s["risk_pct"]) + "%)")
    print("  votes         : " + str(s.get("votes_long", 0)) + "L / " +
          str(s.get("votes_short", 0)) + "S")
    ws = datetime.fromtimestamp(s["window_start_ts"] / 1000, tz=timezone.utc)
    we = datetime.fromtimestamp(s["window_end_ts"] / 1000, tz=timezone.utc)
    print("  window        : " + ws.strftime("%Y-%m-%d %H:%M") + " -> " +
          we.strftime("%H:%M") + " UTC")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    ap.add_argument("--account", type=float, default=1000.0)
    ap.add_argument("--risk",    type=float, default=1.0)
    args = ap.parse_args()

    symbols = [x.strip().upper() for x in args.symbols.split(",") if x.strip()]
    now = datetime.now(timezone.utc)

    if not DB_PATH.exists():
        print("DB not found: " + str(DB_PATH))
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
        print("  time    : " + now.strftime("%Y-%m-%d %H:%M UTC"))
        print("  symbols : " + ", ".join(symbols))
        print("  account : $" + format(args.account, ".2f") +
              "   risk " + str(args.risk) + "%")

        setups = generate_setups(conn, symbols, args.account, args.risk, now)
        if not setups:
            print()
            print("  no setups today")
            return 0

        print()
        print("  found " + str(len(setups)) + " setups")
        for s in setups:
            print_setup(s)

        save_setups(conn, setups)
        print()
        print("  saved " + str(len(setups)) + " setups to trade_setups")

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / (now.strftime("%Y-%m-%d") + ".json")
        path.write_text(json.dumps({
            "date": now.strftime("%Y-%m-%d"),
            "generated_at": now.isoformat(),
            "setups": setups,
        }, indent=2, default=str), encoding="utf-8")
        print("  wrote " + str(path))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
