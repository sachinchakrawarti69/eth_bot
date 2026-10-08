-- Implied volatility surface.

CREATE TABLE IF NOT EXISTS implied_volatility (
    underlying TEXT    NOT NULL,
    expiry     INTEGER NOT NULL,
    strike     REAL    NOT NULL,
    kind       TEXT    NOT NULL,
    ts         INTEGER NOT NULL,
    iv         REAL    NOT NULL,
    iv_fit     REAL,
    moneyness  REAL,
    dte        REAL,
    PRIMARY KEY (underlying, expiry, strike, kind, ts)
);

CREATE INDEX IF NOT EXISTS idx_iv_lookup
    ON implied_volatility (underlying, ts DESC);
