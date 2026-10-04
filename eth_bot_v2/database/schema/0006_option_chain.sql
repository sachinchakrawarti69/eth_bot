-- Option chain snapshots.
CREATE TABLE IF NOT EXISTS option_chain (
    underlying TEXT    NOT NULL,
    expiry     INTEGER NOT NULL,
    strike     REAL    NOT NULL,
    kind       TEXT    NOT NULL,   -- 'C' or 'P'
    ts         INTEGER NOT NULL,
    mark_price REAL,
    bid        REAL,
    ask        REAL,
    iv         REAL,
    oi         REAL,
    volume     REAL,
    PRIMARY KEY (underlying, expiry, strike, kind, ts)
);
CREATE INDEX IF NOT EXISTS idx_option_ts
    ON option_chain (underlying, ts DESC);
