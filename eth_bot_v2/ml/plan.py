"""Turn an ML prediction into a trade plan with levels."""

from __future__ import annotations
from datetime import datetime, timezone, timedelta

from ml.predict import predict


def build_plan(symbol, account=1000.0, risk_pct=1.0, min_conf=0.30):
    p = predict(symbol)

    price = p["price"]                     # live price
    atr   = p["atr"] or (price * 0.02)
    conf  = p["confidence"]

    if conf < min_conf:
        return {
            "symbol":     symbol,
            "action":     "FLAT",
            "reason":     "low confidence (" + format(conf, ".2f") + ")",
            "price":      price,
            "live":       p.get("live", False),
            "confidence": conf,
            "prob_up":    p["prob_up"],
        }

    direction = "LONG" if p["direction"] == "UP" else "SHORT"

    stop_dist   = 1.5 * atr
    target_dist = 2.0 * stop_dist

    if direction == "LONG":
        entry, stop, target = price, price - stop_dist, price + target_dist
    else:
        entry, stop, target = price, price + stop_dist, price - target_dist

    rr = abs(target - entry) / abs(entry - stop) if entry != stop else 0

    risk_usd = account * risk_pct / 100
    size     = risk_usd / stop_dist if stop_dist > 0 else 0

    now = datetime.now(timezone.utc)
    ws  = now
    we  = now + timedelta(hours=24)

    return {
        "symbol":       symbol,
        "action":       direction,
        "reason":       "ML prob_up=" + format(p["prob_up"], ".2f"),
        "price":        price,
        "stale_price":  p.get("stale_price", price),
        "live":         p.get("live", False),
        "confidence":   conf,
        "prob_up":      p["prob_up"],
        "prob_down":    p["prob_down"],
        "regime":       p["regime"],
        "rsi_14":       p["rsi_14"],
        "atr":          atr,
        "entry":        round(entry, 4),
        "stop":         round(stop, 4),
        "target":       round(target, 4),
        "rr":           round(rr, 2),
        "size_units":   round(size, 6),
        "risk_usd":     round(risk_usd, 2),
        "account":      account,
        "risk_pct":     risk_pct,
        "window_start": ws.isoformat(),
        "window_end":   we.isoformat(),
    }


def print_plan(plan):
    if plan is None:
        print("  no plan")
        return

    action = plan["action"]
    if action == "LONG":
        color = "\033[32m"
    elif action == "SHORT":
        color = "\033[31m"
    else:
        color = "\033[90m"
    reset = "\033[0m"

    print()
    print("=" * 66)
    print("  " + color + format(action, "^62") + reset)
    print("  " + plan["symbol"] + "  via ML model")
    print("=" * 66)

    live_tag = "  [LIVE]" if plan.get("live") else "  [STALE]"
    print("  price        : " + format(plan["price"], ">14,.2f") + live_tag)
    print("  confidence   : " + format(plan["confidence"], ".3f"))
    print("  prob_up      : " + format(plan["prob_up"] * 100, ".1f") + "%")
    print("  prob_down    : " + format(plan["prob_down"] * 100, ".1f") + "%")

    if action != "FLAT":
        print()
        print("  entry        : " + format(plan["entry"], ">14,.2f"))
        print("  stop         : " + format(plan["stop"], ">14,.2f"))
        print("  target       : " + format(plan["target"], ">14,.2f"))
        print("  R:R          : " + format(plan["rr"], ">14.2f"))
        print("  size         : " + format(plan["size_units"], ">14.6f") + " units")
        print("  risk         : $" + format(plan["risk_usd"], ">13,.2f"))
        print("  window start : " + plan["window_start"])
        print("  window end   : " + plan["window_end"])
    else:
        print()
        print("  reason       : " + plan["reason"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="ETHUSDT")
    ap.add_argument("--account", type=float, default=1000.0)
    ap.add_argument("--risk",    type=float, default=1.0)
    ap.add_argument("--min-conf", type=float, default=0.30)
    args = ap.parse_args()

    p = build_plan(args.symbol, args.account, args.risk, args.min_conf)
    print_plan(p)
