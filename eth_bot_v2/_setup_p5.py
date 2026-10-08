from pathlib import Path

ROOT = Path(__file__).resolve().parent

SCHEMA = '''-- Phase 5 - backtest trade log and runs.

CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    strategy        TEXT    NOT NULL,
    ts              INTEGER NOT NULL,
    symbols         TEXT,
    start_ts        INTEGER,
    end_ts          INTEGER,
    n_trades        INTEGER,
    win_rate        REAL,
    avg_win         REAL,
    avg_loss        REAL,
    expectancy      REAL,
    expectancy_net  REAL,
    total_return    REAL,
    sharpe          REAL,
    max_dd          REAL,
    profit_factor   REAL,
    n_years_pos     INTEGER,
    n_years_total   INTEGER,
    verdict         TEXT
);

CREATE INDEX IF NOT EXISTS idx_bt_runs_ts ON backtest_runs (ts DESC);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL,
    symbol          TEXT    NOT NULL,
    entry_ts        INTEGER NOT NULL,
    exit_ts         INTEGER NOT NULL,
    direction       TEXT    NOT NULL,
    entry_price     REAL    NOT NULL,
    exit_price      REAL    NOT NULL,
    return_gross    REAL    NOT NULL,
    return_net      REAL    NOT NULL,
    reason_entry    TEXT,
    reason_exit     TEXT,
    signal_name     TEXT
);

CREATE INDEX IF NOT EXISTS idx_bt_trades_run ON backtest_trades (run_id, entry_ts);
'''

BACKTEST = open(ROOT / "_backtest_src.py", "r", encoding="utf-8").read() if (ROOT / "_backtest_src.py").exists() else None

# write schema
schema_path = ROOT / "database" / "schema" / "0018_backtest_trades.sql"
schema_path.parent.mkdir(parents=True, exist_ok=True)
schema_path.write_text(SCHEMA, encoding="utf-8")
print("wrote", schema_path.relative_to(ROOT))
print()
print("Now create scripts_python/backtest.py manually with the code")
print("from the previous message (the big BACKTEST string).")