-- Phase 6 - trade setups (one row per day/symbol/strategy).

CREATE TABLE IF NOT EXISTS trade_setups (
    date            TEXT    NOT NULL,
    symbol          TEXT    NOT NULL,
    strategy        TEXT    NOT NULL,
    direction       TEXT    NOT NULL,
    created_ts      INTEGER NOT NULL,
    current_price   REAL,
    entry           REAL,
    stop            REAL,
    target          REAL,
    rr              REAL,
    size_units      REAL,
    risk_usd        REAL,
    account_usd     REAL,
    risk_pct        REAL,
    trigger_text    TEXT,
    trigger_price   REAL,
    window_start_ts INTEGER,
    window_end_ts   INTEGER,
    expiry_ts       INTEGER,
    confidence      REAL,
    status          TEXT    DEFAULT 'pending',
    triggered_ts    INTEGER,
    filled_ts       INTEGER,
    result          TEXT,
    result_ret      REAL,
    PRIMARY KEY (date, symbol, strategy)
);

CREATE INDEX IF NOT EXISTS idx_setups_date
    ON trade_setups (date);

CREATE INDEX IF NOT EXISTS idx_setups_status
    ON trade_setups (status, date);
