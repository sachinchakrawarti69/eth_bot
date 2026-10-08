-- Phase 3 - support/resistance levels.
-- One row per (symbol, timeframe, ts, level, source).

CREATE TABLE IF NOT EXISTS sr_levels (
    symbol      TEXT    NOT NULL,
    ts          INTEGER NOT NULL,       -- ms epoch when computed
    timeframe   TEXT    NOT NULL,       -- '1h', '4h', '1d'
    level       REAL    NOT NULL,       -- price level
    kind        TEXT    NOT NULL,       -- 'support' | 'resistance'
    source      TEXT    NOT NULL,       -- 'swing','ma','volume','pdh','fib','round','options','liq'
    strength    REAL,                   -- 0.0 to 1.0
    touches     INTEGER,                -- how many times respected
    last_test   INTEGER,                -- ms epoch of last touch
    confluence  INTEGER,                -- sources agreeing at this level
    distance_pct REAL,                  -- distance from current price at ts
    PRIMARY KEY (symbol, ts, timeframe, level, source)
);

CREATE INDEX IF NOT EXISTS idx_sr_lookup
    ON sr_levels (symbol, timeframe, ts DESC, level);

CREATE INDEX IF NOT EXISTS idx_sr_by_time
    ON sr_levels (symbol, timeframe, level, ts DESC);
