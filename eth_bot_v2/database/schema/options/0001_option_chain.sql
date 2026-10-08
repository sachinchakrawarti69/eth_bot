-- Raw option chain snapshots (per instrument).

CREATE TABLE IF NOT EXISTS option_chain (
    underlying    TEXT    NOT NULL,   -- 'ETH', 'BTC'
    expiry        INTEGER NOT NULL,   -- ms epoch of expiry
    strike        REAL    NOT NULL,
    kind          TEXT    NOT NULL,   -- 'C' or 'P'
    ts            INTEGER NOT NULL,   -- snapshot time (ms epoch)
    mark_price    REAL,
    bid           REAL,
    ask           REAL,
    bid_iv        REAL,
    ask_iv        REAL,
    mark_iv       REAL,
    oi            REAL,
    volume        REAL,
    underlying_px REAL,
    PRIMARY KEY (underlying, expiry, strike, kind, ts)
);

CREATE INDEX IF NOT EXISTS idx_chain_lookup
    ON option_chain (underlying, ts DESC);

CREATE INDEX IF NOT EXISTS idx_chain_expiry
    ON option_chain (underlying, expiry, ts DESC);
