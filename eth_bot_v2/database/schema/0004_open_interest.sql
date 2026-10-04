-- Open interest snapshots.
CREATE TABLE IF NOT EXISTS open_interest (
    symbol    TEXT    NOT NULL,
    ts        INTEGER NOT NULL,
    oi        REAL    NOT NULL,
    oi_value  REAL,
    PRIMARY KEY (symbol, ts)
);
CREATE INDEX IF NOT EXISTS idx_oi_ts
    ON open_interest (symbol, ts DESC);
