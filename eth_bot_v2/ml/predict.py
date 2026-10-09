"""Predict next-24h direction using a trained model.

Uses LIVE price from Binance ticker if available, falls back to
the last features-table close.
"""

from __future__ import annotations
import json
import sqlite3
import urllib.request
from pathlib import Path

import joblib
import pandas as pd


ROOT       = Path(__file__).resolve().parents[1]
DB_PATH    = ROOT / "database" / "market.db"
MODELS_DIR = ROOT / "ml" / "_models"


def load_model(symbol):
    p = MODELS_DIR / (symbol + ".joblib")
    if not p.exists():
        raise RuntimeError("model not found for " + symbol)
    return joblib.load(p)


def load_latest_features(symbol):
    with sqlite3.connect(DB_PATH) as c:
        df = pd.read_sql_query(
            "SELECT * FROM features WHERE symbol=? ORDER BY ts DESC LIMIT 1",
            c, params=(symbol,))
    if df.empty:
        raise RuntimeError("no features for " + symbol)
    return df.iloc[0].copy()


def get_live_price(symbol):
    """Get current price from Binance ticker. Returns None on failure."""
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=" + symbol
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        return float(data["price"])
    except Exception:
        try:
            # fallback mirror
            url = "https://data-api.binance.vision/api/v3/ticker/price?symbol=" + symbol
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode("utf-8"))
            return float(data["price"])
        except Exception:
            return None


def build_input_row(row, feats):
    r = row.copy()
    if "regime_enc" in feats:
        regime_map = {"bull": 2, "chop": 1, "bear": 0}
        r["regime_enc"] = regime_map.get(r.get("regime"), 1)
    missing = [f for f in feats if f not in r.index]
    if missing:
        raise RuntimeError("features missing from row: " + str(missing))
    X = pd.DataFrame([r[feats].values], columns=feats)
    X = X.fillna(0)
    return X


def predict(symbol):
    bundle = load_model(symbol)
    model  = bundle["model"]
    feats  = bundle["features"]

    row = load_latest_features(symbol)
    X   = build_input_row(row, feats)

    proba = float(model.predict_proba(X)[0, 1])
    pred  = int(proba > 0.5)

    # fetch live price
    live = get_live_price(symbol)
    stale_price = float(row["close"])
    price = live if live is not None else stale_price

    return {
        "symbol":       symbol,
        "ts":           int(row["ts"]),
        "price":        price,
        "stale_price":  stale_price,
        "live":         live is not None,
        "direction":    "UP" if pred == 1 else "DOWN",
        "prob_up":      proba,
        "prob_down":    1 - proba,
        "confidence":   abs(proba - 0.5) * 2,
        "atr":          float(row["atr_14"]) if pd.notna(row["atr_14"]) else None,
        "rsi_14":       float(row["rsi_14"]) if pd.notna(row["rsi_14"]) else None,
        "regime":       row.get("regime"),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="ETHUSDT")
    args = ap.parse_args()

    out = predict(args.symbol)
    print("  symbol     : " + out["symbol"])
    print("  price      : " + format(out["price"], ",.2f") +
          ("  (live)" if out["live"] else "  (stale)"))
    if out["live"]:
        print("  candle     : " + format(out["stale_price"], ",.2f") + "  (last 1h close)")
    print("  direction  : " + out["direction"])
    print("  prob up    : " + format(out["prob_up"] * 100, ".1f") + "%")
    print("  prob down  : " + format(out["prob_down"] * 100, ".1f") + "%")
    print("  confidence : " + format(out["confidence"], ".3f"))
    print("  regime     : " + str(out["regime"]))


if __name__ == "__main__":
    main()
