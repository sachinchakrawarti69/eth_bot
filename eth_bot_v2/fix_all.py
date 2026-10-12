"""
fix_all.py -- clean up eth_bot_v2 tree and create missing pieces.

Fixes:
  1. remove dead folders (data_pipeline, scripts, engine, models, server, tools, storage)
  2. remove Excel lock files
  3. rename duplicate migrations (0014_option_summary -> 0020)
  4. rename backtest.py -> backtest_features.py
  5. move notebook 11_options.ipynb -> option_notebook/10_options_extra.ipynb
  6. delete stray docs (cmd.md, cmd_2.md, ggg.md, rdmap.md)
  7. remove all __pycache__
  8. create missing data/ and reports/ subfolders
  9. write trader/ package if missing
 10. write .gitignore if missing
 11. verify required ML model files exist
 12. final tree print

Run:
    python fix_all.py
"""

from __future__ import annotations
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


# ================================================================
#  HELPERS
# ================================================================

def section(msg):
    print()
    print("=" * 66)
    print("  " + msg)
    print("=" * 66)


def rm(rel, reason=""):
    p = ROOT / rel
    if not p.exists():
        print("  skip (missing) " + rel)
        return
    try:
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        else:
            p.unlink(missing_ok=True)
        print("  removed " + rel + ("  " + reason if reason else ""))
    except Exception as e:
        print("  FAIL " + rel + ": " + str(e))


def rename(rel_old, rel_new):
    p_old = ROOT / rel_old
    p_new = ROOT / rel_new
    if not p_old.exists():
        print("  skip (missing) " + rel_old)
        return
    if p_new.exists():
        print("  skip (dest exists) " + rel_new)
        return
    try:
        p_new.parent.mkdir(parents=True, exist_ok=True)
        p_old.rename(p_new)
        print("  renamed " + rel_old + " -> " + rel_new)
    except Exception as e:
        print("  FAIL rename " + rel_old + ": " + str(e))


def mkdir(rel):
    p = ROOT / rel
    if p.exists():
        print("  ok " + rel)
        return
    p.mkdir(parents=True, exist_ok=True)
    print("  created " + rel)


def write(path_rel, content):
    p = ROOT / path_rel
    if p.exists() and not p.read_text(encoding="utf-8").strip() == "":
        # don't overwrite non-empty files
        print("  keep  " + path_rel + "  (exists)")
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print("  wrote " + path_rel + "  (" + str(content.count(chr(10)) + 1) + " lines)")


# ================================================================
#  FILE CONTENTS
# ================================================================

GITIGNORE = """# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual envs
.venv/
venv/
env/
ENV/

# Database WAL files
*.db-wal
*.db-shm
*.db.bak

# Excel lock files
~$*.xlsx

# Outputs (regenerated)
eth_bot_v2/exports/*.xlsx
eth_bot_v2/exports/*.csv
eth_bot_v2/reports/**/*.json
eth_bot_v2/reports/**/*.md
eth_bot_v2/reports/**/*.png
eth_bot_v2/ml/_models/*.joblib

# Logs
*.log
logs/

# Env
.env
.env.*

# Jupyter
.ipynb_checkpoints/

# OS
.DS_Store
Thumbs.db
"""


TRADER_INIT = '"""Live trading signals."""\n'


TRADER_SIGNAL = '''"""Generate today's live trade signal."""

from __future__ import annotations
import sqlite3
from pathlib import Path

import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"


def load_daily(symbol):
    with sqlite3.connect(DB_PATH) as c:
        df = pd.read_sql_query(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlcv WHERE symbol=? AND timeframe='1d' "
            "ORDER BY open_time",
            c, params=(symbol,))
    if df.empty:
        raise RuntimeError("no daily data for " + symbol)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.drop(columns=["open_time"]).set_index("date")
    return df


def add_indicators(df):
    df = df.copy()
    df["sma_50"]  = df["close"].rolling(50).mean()
    df["sma_200"] = df["close"].rolling(200).mean()
    df["ema_12"]  = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"]  = df["close"].ewm(span=26, adjust=False).mean()
    macd = df["ema_12"] - df["ema_26"]
    df["macd_hist"] = macd - macd.ewm(span=9, adjust=False).mean()

    d  = df["close"].diff()
    up = d.clip(lower=0).rolling(14).mean()
    dn = (-d.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - 100 / (1 + up / dn.replace(0, float("nan")))

    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"]  - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()

    df["bull"] = (df["close"] > df["sma_50"]) & (df["sma_50"] > df["sma_200"])
    return df.dropna()


def current_signal(symbol):
    df = load_daily(symbol)
    df = add_indicators(df)
    if df.empty:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    bull      = bool(last["bull"])
    macd_hist = float(last["macd_hist"])
    prev_macd = float(prev["macd_hist"])

    if bull and macd_hist > 0 and prev_macd <= 0:
        action = "BUY"
        reason = "bull trend + MACD turned positive"
    elif bull and macd_hist > 0:
        action = "HOLD"
        reason = "bull trend + MACD positive"
    elif not bull and macd_hist < 0:
        action = "EXIT"
        reason = "trend broke + MACD negative"
    else:
        action = "WAIT"
        reason = "conditions not met"

    return {
        "symbol":    symbol,
        "date":      df.index[-1].date().isoformat(),
        "price":     float(last["close"]),
        "action":    action,
        "reason":    reason,
        "bull":      bull,
        "macd_hist": macd_hist,
        "rsi_14":    float(last["rsi_14"]),
        "sma_50":    float(last["sma_50"]),
        "sma_200":   float(last["sma_200"]),
        "atr_14":    float(last["atr_14"]),
    }
'''


TRADER_PLAN = '''"""Turn a signal into a complete trade plan."""

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
        "BUY":  "\\033[1;32m",
        "HOLD": "\\033[1;33m",
        "EXIT": "\\033[1;31m",
        "WAIT": "\\033[90m",
    }.get(action, "")
    reset = "\\033[0m"

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
'''


TRADER_RUN = '''"""CLI: check today's signals.

Usage:
    python -m trader.run
    python -m trader.run --symbols BTCUSDT,ETHUSDT
    python -m trader.run --account 5000 --risk 2.0
"""

from __future__ import annotations
import argparse

from trader.plan import build, print_plan, save


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    ap.add_argument("--account", type=float, default=1000.0)
    ap.add_argument("--risk", type=float, default=2.0)
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    print("=" * 66)
    print("  DAILY TRADE SIGNAL")
    print("=" * 66)
    print("  strategy: trend_follow")
    print("  rule    : buy bull regime + MACD>0, hold 30 days")
    print("  account : $" + format(args.account, ",.2f"))
    print("  risk    : " + str(args.risk) + "% per trade")

    for sym in symbols:
        try:
            p = build(sym, args.account, args.risk)
            print_plan(p)
            path = save(p)
            if path:
                print("  saved: " + str(path))
        except Exception as e:
            print()
            print("  [" + sym + "] error: " + type(e).__name__ + ": " + str(e))


if __name__ == "__main__":
    main()
'''


RUN_DAILY_BAT = """@echo off
cd /d "%~dp0"

echo ==== UPDATE DATA ====
python -m scripts_python.fetchers.multi
python -m scripts_python.fetchers.futures
python -m scripts_python.fetchers.funding

echo.
echo ==== BUILD FEATURES ====
python -m scripts_python.builders.features

echo.
echo ==== TRADE SIGNAL ====
python -m trader.run

echo.
pause
"""


# ================================================================
#  MAIN
# ================================================================

def main():
    print("=" * 66)
    print("  FIX ALL")
    print("=" * 66)
    print("  root: " + str(ROOT))

    # ------------------------------------------------------------
    section("1. remove dead folders")
    rm("data_pipeline", "(unused scaffold)")
    rm("scripts", "(unused collectors)")
    rm("engine", "(empty)")
    rm("models", "(empty)")
    rm("server", "(empty)")
    rm("tools", "(empty)")
    rm("storage", "(empty)")
    rm("data/models", "(old tensorboard logs)")

    # ------------------------------------------------------------
    section("2. remove Excel lock files")
    exports = ROOT / "exports"
    if exports.exists():
        n = 0
        for f in exports.glob("~$*.xlsx"):
            try:
                f.unlink()
                print("  removed exports/" + f.name)
                n += 1
            except Exception as e:
                print("  FAIL exports/" + f.name + ": " + str(e))
        if n == 0:
            print("  (no lock files)")
    else:
        print("  exports/ not found")

    # ------------------------------------------------------------
    section("3. rename duplicate migration")
    rename("database/schema/0014_option_summary.sql",
           "database/schema/0020_option_summary.sql")

    # ------------------------------------------------------------
    section("4. rename backtest.py")
    rename("scripts_python/backtest.py",
           "scripts_python/backtest_features.py")

    # ------------------------------------------------------------
    section("5. move notebook 11")
    nb_old = ROOT / "analysis" / "notebooks" / "11_options.ipynb"
    nb_new = ROOT / "analysis" / "option_notebook" / "10_options_extra.ipynb"
    if nb_old.exists() and not nb_new.exists():
        nb_new.parent.mkdir(parents=True, exist_ok=True)
        nb_old.rename(nb_new)
        print("  moved 11_options.ipynb -> option_notebook/10_options_extra.ipynb")
    else:
        print("  skip (already moved or missing)")

    # ------------------------------------------------------------
    section("6. delete stray docs")
    rm("docs/cmd.md", "(superseded)")
    rm("docs/cmd_2.md", "(superseded)")
    rm("docs/rdmap.md", "(typo)")
    rename("docs/ggg.md", "docs/notes.md")

    # ------------------------------------------------------------
    section("7. remove __pycache__")
    removed = 0
    for d in list(ROOT.rglob("__pycache__")):
        try:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
        except Exception:
            pass
    print("  removed " + str(removed) + " cache folders")

    # ------------------------------------------------------------
    section("8. ensure data/ subfolders")
    for sub in ("data", "data/raw", "data/processed", "data/state"):
        mkdir(sub)

    # ------------------------------------------------------------
    section("9. ensure reports/ subfolders")
    for sub in (
        "reports",
        "reports/backtest6y",
        "reports/daily",
        "reports/forecasts",
        "reports/ml_plans",
        "reports/orders",
        "reports/predictions",
        "reports/trade_signals",
    ):
        mkdir(sub)

    # ------------------------------------------------------------
    section("10. write trader/ package")
    write("trader/__init__.py", TRADER_INIT)
    write("trader/signal.py",   TRADER_SIGNAL)
    write("trader/plan.py",     TRADER_PLAN)
    write("trader/run.py",      TRADER_RUN)

    # ------------------------------------------------------------
    section("11. write .gitignore")
    write(".gitignore", GITIGNORE)

    # ------------------------------------------------------------
    section("12. write run_daily.bat")
    write("run_daily.bat", RUN_DAILY_BAT)

    # ------------------------------------------------------------
    section("13. verify ML models")
    models_dir = ROOT / "ml" / "_models"
    if not models_dir.exists():
        print("  ML MODELS FOLDER MISSING: " + str(models_dir))
    else:
        for sym in ("BTCUSDT", "ETHUSDT"):
            joblib = models_dir / (sym + ".joblib")
            json_f = models_dir / (sym + ".json")
            tag = "ok" if joblib.exists() else "MISSING"
            print("  " + sym + "  joblib=" + tag +
                  "  json=" + ("ok" if json_f.exists() else "MISSING"))
        print()
        print("  if joblib missing, retrain:")
        print("    python -m ml.train --symbol ETHUSDT")
        print("    python -m ml.train --symbol BTCUSDT")

    # ------------------------------------------------------------
    section("14. final top-level tree")
    for p in sorted(ROOT.iterdir()):
        if p.name.startswith("."):
            continue
        mark = "/" if p.is_dir() else ""
        print("  " + p.name + mark)

    # ------------------------------------------------------------
    section("DONE")
    print("  Fix applied.")
    print()
    print("  Next:")
    print("    python -m trader.run                     # get today's signal")
    print("    python -m ml.predict --symbol ETHUSDT    # ML prediction")
    print("    python -m bt6.run --symbols ETHUSDT      # backtest")
    print()
    print("  Delete this script when done:")
    print("    Remove-Item fix_all.py")
    print()


if __name__ == "__main__":
    main()