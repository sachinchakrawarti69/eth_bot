-- Perpetual funding rates.
CREATE TABLE IF NOT EXISTS funding_rate (
    symbol TEXT    NOT NULL,
    ts     INTEGER NOT NULL,
    rate   REAL    NOT NULL,
    PRIMARY KEY (symbol, ts)
);
CREATE INDEX IF NOT EXISTS idx_funding_ts
    ON funding_rate (symbol, ts DESC);
