from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "scripts_python" / "opportunity.py"

src = TARGET.read_text(encoding="utf-8")

# find the generate() function and replace it
OLD_MARKER_START = "def generate(conn, symbols, account, risk_pct, now_utc):"
OLD_MARKER_END   = "def save(conn, setups):"

start = src.find(OLD_MARKER_START)
end   = src.find(OLD_MARKER_END)

if start == -1 or end == -1:
    print("ERROR: could not find generate() function")
    raise SystemExit(1)

NEW_GENERATE = '''def generate(conn, symbols, account, risk_pct, now_utc):
    out = []
    date_str = now_utc.strftime("%Y-%m-%d")

    for sym in symbols:
        _, last = load_latest_features(conn, sym)
        if last is None:
            continue
        price = float(last["close"])
        atr = float(last["atr_14"]) if pd.notna(last["atr_14"]) else price * 0.02

        # collect ALL candidate signals for this symbol
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

            entry, stop, target = raw["entry"], raw["stop"], raw["target"]
            rr = abs(target - entry) / abs(entry - stop) if entry != stop else 0
            units, risk_usd = compute_size(account, risk_pct, entry, stop)
            ws, we = compute_window(now_utc)

            conf = 0.5
            if last["regime"] == "bull" and raw["direction"] == "LONG":
                conf += 0.1
            if pd.notna(last.get("rsi_14")) and last["rsi_14"] < 25:
                conf += 0.1

            candidates.append({
                "strategy": name,
                "direction": raw["direction"],
                "entry": entry, "stop": stop, "target": target,
                "rr": rr, "units": units, "risk_usd": risk_usd,
                "window_start": ws, "window_end": we,
                "hold": raw["hold"],
                "confidence": conf,
            })

        if not candidates:
            continue

        # arbitrate: one direction per symbol
        longs  = [c for c in candidates if c["direction"] == "LONG"]
        shorts = [c for c in candidates if c["direction"] == "SHORT"]

        if len(longs) > len(shorts):
            winner = max(longs, key=lambda x: x["confidence"])
        elif len(shorts) > len(longs):
            winner = max(shorts, key=lambda x: x["confidence"])
        else:
            # tie - no clear edge
            continue

        out.append({
            "date": date_str,
            "symbol": sym,
            "strategy": winner["strategy"],
            "direction": winner["direction"],
            "created_ts": int(now_utc.timestamp() * 1000),
            "current_price": price,
            "entry": round(winner["entry"], 4),
            "stop": round(winner["stop"], 4),
            "target": round(winner["target"], 4),
            "rr": round(winner["rr"], 2),
            "size_units": round(winner["units"], 6),
            "risk_usd": round(winner["risk_usd"], 2),
            "account_usd": account,
            "risk_pct": risk_pct,
            "trigger_text": "price " + ("<=" if winner["direction"] == "LONG" else ">=") + " " + format(winner["entry"], ".2f"),
            "trigger_price": round(winner["entry"], 4),
            "window_start_ts": int(winner["window_start"].timestamp() * 1000),
            "window_end_ts": int(winner["window_end"].timestamp() * 1000),
            "expiry_ts": int((winner["window_end"] + timedelta(hours=winner["hold"])).timestamp() * 1000),
            "confidence": round(winner["confidence"], 2),
        })

    return out


'''

new_src = src[:start] + NEW_GENERATE + src[end:]
TARGET.write_text(new_src, encoding="utf-8")

print("patched", TARGET)
print("bytes:", TARGET.stat().st_size)

import ast
ast.parse(new_src)
print("syntax OK")