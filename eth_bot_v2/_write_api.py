"""Write scripts_python/web/api.py - Flask backend for the HTML UI."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "scripts_python" / "web" / "api.py"

CODE = r'''"""Trade Desk API - Flask backend for web UI.

Serves:
    GET  /api/prices              live Binance ticker
    GET  /api/setups?date=...     today's setups from DB
    GET  /api/candles?symbol=...  last N 1h candles
    POST /api/scan                run opportunity scanner

Run:
    python scripts_python/web/api.py
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS


ROOT    = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "market.db"

app = Flask(__name__)
CORS(app)

PRICE_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


# ================================================================
#  prices
# ================================================================

@app.route("/api/prices")
def prices():
    out = {}
    for sym in PRICE_SYMBOLS:
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}"
            with urllib.request.urlopen(url, timeout=5) as r:
                d = json.loads(r.read().decode("utf-8"))
            out[sym] = {
                "price":  float(d["lastPrice"]),
                "change": float(d["priceChangePercent"]),
                "high":   float(d["highPrice"]),
                "low":    float(d["lowPrice"]),
                "volume": float(d["volume"]),
            }
        except Exception:
            pass
    return jsonify(out)


# ================================================================
#  setups
# ================================================================

@app.route("/api/setups")
def setups():
    date = request.args.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not DB_PATH.exists():
        return jsonify({"setups": []})
    try:
        with sqlite3.connect(DB_PATH) as c:
            rows = c.execute(
                """SELECT date, symbol, strategy, direction, current_price,
                          entry, stop, target, rr, size_units, risk_usd,
                          trigger_text, window_start_ts, window_end_ts,
                          confidence, status
                   FROM trade_setups WHERE date=?
                   ORDER BY confidence DESC""",
                (date,)).fetchall()
        keys = ["date","symbol","strategy","direction","current_price",
                "entry","stop","target","rr","size_units","risk_usd",
                "trigger_text","window_start_ts","window_end_ts",
                "confidence","status"]
        return jsonify({"setups": [dict(zip(keys, r)) for r in rows]})
    except Exception as e:
        return jsonify({"setups": [], "error": str(e)})


# ================================================================
#  candles
# ================================================================

@app.route("/api/candles")
def candles():
    symbol = request.args.get("symbol", "ETHUSDT")
    limit  = int(request.args.get("limit", 200))
    if not DB_PATH.exists():
        return jsonify({"candles": []})
    try:
        with sqlite3.connect(DB_PATH) as c:
            df = pd.read_sql_query(
                """SELECT open_time, open, high, low, close, volume
                   FROM ohlcv WHERE symbol=? AND timeframe='1h'
                   ORDER BY open_time DESC LIMIT ?""",
                c, params=(symbol, limit))
        if df.empty:
            return jsonify({"candles": []})
        df = df.sort_values("open_time")
        df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.strftime(
            "%Y-%m-%d %H:%M")
        out = df[["date","open","high","low","close","volume"]].to_dict("records")
        return jsonify({"candles": out})
    except Exception as e:
        return jsonify({"candles": [], "error": str(e)})


# ================================================================
#  scan
# ================================================================

@app.route("/api/scan", methods=["POST"])
def scan():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "scripts_python.opportunity",
             "--account", "1000", "--risk", "1.0"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=60)
        return jsonify({
            "ok": r.returncode == 0,
            "stdout": r.stdout[-2000:],
            "stderr": r.stderr[-500:],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ================================================================
#  health
# ================================================================

@app.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "db": DB_PATH.exists(),
        "time": datetime.now(timezone.utc).isoformat(),
    })


# ================================================================
#  serve the HTML
# ================================================================

@app.route("/")
def index():
    html = Path(__file__).parent.parent.parent / "web" / "trade_desk.html"
    return html.read_text(encoding="utf-8")


# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  TRADE DESK API")
    print("=" * 60)
    print(f"  DB      : {DB_PATH}")
    print(f"  HTML    : {Path(__file__).parent.parent.parent / 'web' / 'trade_desk.html'}")
    print(f"  serving : http://localhost:8000")
    print()
    app.run(host="0.0.0.0", port=8000, debug=False)
'''

TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(CODE, encoding="utf-8")
print("wrote", TARGET.relative_to(ROOT))
print("size:", len(CODE), "bytes")

import ast
ast.parse(CODE)
print("syntax OK")