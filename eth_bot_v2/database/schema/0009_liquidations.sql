-- Liquidation events.
CREATE TABLE IF NOT EXISTS liquidations (
    symbol TEXT    NOT NULL,
    ts     INTEGER NOT NULL,
    side   TEXT    NOT NULL,   -- 'long' | 'short'
    price  REAL    NOT NULL,
    qty    REAL    NOT NULL,
    value  REAL,
    PRIMARY KEY (symbol, ts, side, price, qty)
);
CREATE INDEX IF NOT EXISTS idx_liq_ts
    ON liquidations (symbol, ts DESC);
