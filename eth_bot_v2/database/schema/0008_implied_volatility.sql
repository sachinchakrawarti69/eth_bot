-- Implied volatility surface points.
CREATE TABLE IF NOT EXISTS implied_volatility (
    underlying TEXT    NOT NULL,
    expiry     INTEGER NOT NULL,
    strike     REAL    NOT NULL,
    kind       TEXT    NOT NULL,
    ts         INTEGER NOT NULL,
    iv         REAL    NOT NULL,
    PRIMARY KEY (underlying, expiry, strike, kind, ts)
);
