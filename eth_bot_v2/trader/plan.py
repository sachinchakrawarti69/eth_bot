"""Turn a signal into a complete trade plan."""

from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from trader.signal import current_signal


ROOT    = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "trade_signals"


def build(symbol, account=1000.0, risk_pct=2.0):
    sig = current_signal(symbol)
    if sig is None:
        return None

    price = sig["price"]
    atr = sig["atr_14"]
    action = sig["action"]

    stop_dist = 2.0 * atr
    target_dist = 3.0 * stop_dist

    if action == "BUY":
        entry  = price
        stop   = price - stop_dist
        target = price + target_dist
    else:
        entry = price
        stop = None
        target = None

    risk_usd = account * risk_pct / 100
    size_units = (risk_usd / stop_dist) if (action == "BUY" and stop_dist > 0) else 0.0

    now = datetime.now(timezone.utc)
    ws = now
    we = now + timedelta(days=30)

    return {
        "symbol":       symbol,
        "date":         sig["date"],
        "action":       action,
        "reason":       sig["reason"],
        "price":        price,
        "bull":         sig["bull"],
        "macd_hist":    sig["macd_hist"],
        "rsi_14":       sig["rsi_14"],
        "sma_50":       sig["sma_50"],
        "sma_200":      sig["sma_200"],
        "atr_14":       atr,
        "entry":        entry,
        "stop":         stop,
        "target":       target,
        "stop_dist":    stop_dist,
        "rr":           3.0 if action == "BUY" else 0.0,
        "size_units":   round(size_units, 6),
        "risk_usd":     risk_usd,
        "account":      account,
        "risk_pct":     risk_pct,
        "hold_days":    30,
        "window_start": ws.isoformat(),
        "window_end":   we.isoformat(),
    }


def print_plan(p):
    if p is None:
        print("  no plan")
        return

    action = p["action"]
    color = {
        "BUY":  "\033[1;32m",
        "HOLD": "\033[1;33m",
        "EXIT": "\033[1;31m",
        "WAIT": "\033[90m",
    }.get(action, "")
    reset = "\033[0m"

    print()
    print("=" * 66)
    print("  " + color + format(action, "^62") + reset)
    print("  " + p["symbol"] + "  --  " + p["date"])
    print("=" * 66)
    print("  price        : " + format(p["price"], ">14,.2f"))
    print("  reason       : " + p["reason"])
    print()
    print("  bull trend   : " + ("YES" if p["bull"] else "NO"))
    print("  macd hist    : " + format(p["macd_hist"], "+.3f"))
    print("  rsi_14       : " + format(p["rsi_14"], ".1f"))
    print("  sma_50       : " + format(p["sma_50"], ">14,.2f"))
    print("  sma_200      : " + format(p["sma_200"], ">14,.2f"))
    print("  atr_14       : " + format(p["atr_14"], ".2f"))

    if action == "BUY":
        print()
        print("  entry        : " + format(p["entry"], ">14,.2f"))
        print("  stop         : " + format(p["stop"], ">14,.2f") +
              "   (" + format((p["stop"] - p["entry"]) / p["entry"] * 100, ".2f") + "%)")
        print("  target       : " + format(p["target"], ">14,.2f") +
              "   (+" + format((p["target"] - p["entry"]) / p["entry"] * 100, ".2f") + "%)")
        print("  R:R          : " + format(p["rr"], ".2f") + " : 1")
        print("  size         : " + format(p["size_units"], ">14.6f") + " units")
        print("  risk         : $" + format(p["risk_usd"], ",.2f") +
              "  (" + str(p["risk_pct"]) + "% of $" + format(p["account"], ",.0f") + ")")
        print("  hold         : " + str(p["hold_days"]) + " days")
        print("  exit when    : close < SMA50  OR  MACD hist < 0")
    elif action == "HOLD":
        print()
        print("  stay in position. no action needed.")
    elif action == "EXIT":
        print()
        print("  close any open position now.")


def save(p):
    if p is None:
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / (p["date"] + "_" + p["symbol"] + ".json")
    path.write_text(json.dumps(p, indent=2, default=str), encoding="utf-8")
    return path
