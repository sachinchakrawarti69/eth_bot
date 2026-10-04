-- Option greeks per (expiry, strike, kind).
CREATE TABLE IF NOT EXISTS greeks (
    underlying TEXT    NOT NULL,
    expiry     INTEGER NOT NULL,
    strike     REAL    NOT NULL,
    kind       TEXT    NOT NULL,
    ts         INTEGER NOT NULL,
    delta      REAL,
    gamma      REAL,
    theta      REAL,
    vega       REAL,
    rho        REAL,
    PRIMARY KEY (underlying, expiry, strike, kind, ts)
);
