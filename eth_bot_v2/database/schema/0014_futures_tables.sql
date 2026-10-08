-- Phase 1 - futures data tables.

-- long/short ratio (Binance publishes per 1h)
CREATE TABLE IF NOT EXISTS long_short_ratio (
    symbol      TEXT    NOT NULL,
    ts          INTEGER NOT NULL,
    long_pct    REAL,
    short_pct   REAL,
    ratio       REAL,
    PRIMARY KEY (symbol, ts)
);

CREATE INDEX IF NOT EXISTS idx_ls_lookup
    ON long_short_ratio (symbol, ts DESC);


-- taker buy/sell volume (from ohlcv klines extended)
CREATE TABLE IF NOT EXISTS taker_volume (
    symbol      TEXT    NOT NULL,
    ts          INTEGER NOT NULL,
    taker_buy   REAL,
    taker_sell  REAL,
    buy_ratio   REAL,
    PRIMARY KEY (symbol, ts)
);

CREATE INDEX IF NOT EXISTS idx_taker_lookup
    ON taker_volume (symbol, ts DESC);


-- mark + index price (stress detection)
CREATE TABLE IF NOT EXISTS mark_price (
    symbol          TEXT    NOT NULL,
    ts              INTEGER NOT NULL,
    mark_price      REAL,
    index_price     REAL,
    spread_pct      REAL,
    PRIMARY KEY (symbol, ts)
);

CREATE INDEX IF NOT EXISTS idx_mark_lookup
    ON mark_price (symbol, ts DESC);


-- S/R level tables (Phase 3 will populate)
CREATE TABLE IF NOT EXISTS sr_levels_static (
    symbol      TEXT    NOT NULL,
    ts          INTEGER NOT NULL,
    timeframe   TEXT    NOT NULL,
    level       REAL    NOT NULL,
    kind        TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    strength    REAL,
    touches     INTEGER,
    last_test   INTEGER,
    confluence  INTEGER,
    PRIMARY KEY (symbol, ts, timeframe, level, source)
);

CREATE INDEX IF NOT EXISTS idx_sr_static_lookup
    ON sr_levels_static (symbol, timeframe, ts DESC, level);


CREATE TABLE IF NOT EXISTS sr_levels_dynamic (
    symbol      TEXT    NOT NULL,
    ts          INTEGER NOT NULL,
    timeframe   TEXT    NOT NULL,
    level       REAL    NOT NULL,
    kind        TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    strength    REAL,
    touches     INTEGER,
    last_test   INTEGER,
    confluence  INTEGER,
    PRIMARY KEY (symbol, ts, timeframe, level, source)
);

CREATE INDEX IF NOT EXISTS idx_sr_dynamic_lookup
    ON sr_levels_dynamic (symbol, timeframe, ts DESC, level);
