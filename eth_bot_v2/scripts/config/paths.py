"""
paths.py -- single source of truth for all file and folder paths.

Import:
    from scripts.config.paths import (
        ROOT, DB_PATH, OPTIONS_DB,
        DATA_DIR, RAW_DIR, PROCESSED_DIR, STATE_DIR,
        REPORTS_DIR, EXPORTS_DIR, MODELS_DIR,
        LOGS_DIR, SCHEMA_DIR,
        ensure_dirs,
    )

Every path is a pathlib.Path, resolved to absolute.
"""

from __future__ import annotations
from pathlib import Path


# ================================================================
#  ROOT
# ================================================================
# This file lives at:  <root>/scripts/config/paths.py
# parents[0] = config/
# parents[1] = scripts/
# parents[2] = eth_bot_v2/   ← this is ROOT

ROOT = Path(__file__).resolve().parents[2]


# ================================================================
#  DATABASE
# ================================================================

DATABASE_DIR = ROOT / "database"
DB_PATH      = DATABASE_DIR / "market.db"
OPTIONS_DB   = DATABASE_DIR / "options.db"
SCHEMA_DIR   = DATABASE_DIR / "schema"
CONFIG_API_DIR = DATABASE_DIR / "config" / "api"


# ================================================================
#  DATA
# ================================================================

DATA_DIR       = ROOT / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed"
STATE_DIR      = DATA_DIR / "state"


# ================================================================
#  OUTPUTS
# ================================================================

EXPORTS_DIR    = ROOT / "exports"
REPORTS_DIR    = ROOT / "reports"

REPORTS_DAILY_DIR      = REPORTS_DIR / "daily"
REPORTS_ORDERS_DIR     = REPORTS_DIR / "orders"
REPORTS_FORECASTS_DIR  = REPORTS_DIR / "forecasts"
REPORTS_PREDICT_DIR    = REPORTS_DIR / "predictions"
REPORTS_BACKTEST_DIR   = REPORTS_DIR / "backtest6y"
REPORTS_ML_PLANS_DIR   = REPORTS_DIR / "ml_plans"
REPORTS_SIGNALS_DIR    = REPORTS_DIR / "trade_signals"


# ================================================================
#  MODELS
# ================================================================

MODELS_DIR     = ROOT / "models"
ML_MODELS_DIR  = MODELS_DIR / "ml"


# ================================================================
#  LOGS
# ================================================================

LOGS_DIR       = ROOT / "logs"
LOGS_DAILY_DIR = LOGS_DIR / "daily"
LOGS_ERROR_DIR = LOGS_DIR / "errors"
LOGS_TRADES_DIR = LOGS_DIR / "trades"


# ================================================================
#  SCRIPTS
# ================================================================

SCRIPTS_DIR    = ROOT / "scripts"


# ================================================================
#  WEB
# ================================================================

WEB_DIR        = ROOT / "web"
TRADE_DESK_HTML = WEB_DIR / "trade_desk.html"


# ================================================================
#  ENSURE DIRS EXIST
# ================================================================

ALL_DIRS = [
    DATABASE_DIR,
    DATA_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    STATE_DIR,
    EXPORTS_DIR,
    REPORTS_DIR,
    REPORTS_DAILY_DIR,
    REPORTS_ORDERS_DIR,
    REPORTS_FORECASTS_DIR,
    REPORTS_PREDICT_DIR,
    REPORTS_BACKTEST_DIR,
    REPORTS_ML_PLANS_DIR,
    REPORTS_SIGNALS_DIR,
    MODELS_DIR,
    ML_MODELS_DIR,
    LOGS_DIR,
    LOGS_DAILY_DIR,
    LOGS_ERROR_DIR,
    LOGS_TRADES_DIR,
]


def ensure_dirs() -> None:
    """Create every folder if missing. Safe to call at startup."""
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# ================================================================
#  SELF TEST
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  PATHS")
    print("=" * 60)
    print(f"  ROOT           : {ROOT}")
    print(f"  DB_PATH        : {DB_PATH}   exists={DB_PATH.exists()}")
    print(f"  OPTIONS_DB     : {OPTIONS_DB}   exists={OPTIONS_DB.exists()}")
    print(f"  DATA_DIR       : {DATA_DIR}")
    print(f"  EXPORTS_DIR    : {EXPORTS_DIR}")
    print(f"  REPORTS_DIR    : {REPORTS_DIR}")
    print(f"  ML_MODELS_DIR  : {ML_MODELS_DIR}")
    print(f"  LOGS_DIR       : {LOGS_DIR}")
    print()
    print("  dirs (exists):")
    for d in ALL_DIRS:
        print(f"    {'ok ' if d.exists() else 'NEW'}  {d.relative_to(ROOT)}")
    print()
    print("  running ensure_dirs()...")
    ensure_dirs()
    print("  done.")