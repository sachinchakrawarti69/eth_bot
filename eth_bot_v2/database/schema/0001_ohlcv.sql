-- OHLCV candles.
CREATE TABLE IF NOT EXISTS ohlcv (
    symbol       TEXT    NOT NULL,
    timeframe    TEXT    NOT NULL,
    open_time    INTEGER NOT NULL,
    close_time   INTEGER NOT NULL,
    open         REAL    NOT NULL,
    high         REAL    NOT NULL,
    low          REAL    NOT NULL,
    close        REAL    NOT NULL,
    volume       REAL    NOT NULL,
    quote_volume REAL,
    trades       INTEGER,
    PRIMARY KEY (symbol, timeframe, open_time)
);
CREATE INDEX IF NOT EXISTS idx_ohlcv_lookup
    ON ohlcv (symbol, timeframe, open_time DESC);

CREATE TABLE IF NOT EXISTS _schema_version (
    filename    TEXT PRIMARY KEY,
    applied_at  INTEGER NOT NULL
);
