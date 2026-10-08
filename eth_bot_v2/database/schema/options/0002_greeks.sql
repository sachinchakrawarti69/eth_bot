-- Greeks per instrument snapshot.

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

CREATE INDEX IF NOT EXISTS idx_greeks_lookup
    ON greeks (underlying, ts DESC);
