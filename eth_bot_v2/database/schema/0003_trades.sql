-- Individual trades.
CREATE TABLE IF NOT EXISTS trades (
    symbol         TEXT    NOT NULL,
    trade_id       INTEGER NOT NULL,
    ts             INTEGER NOT NULL,
    price          REAL    NOT NULL,
    qty            REAL    NOT NULL,
    is_buyer_maker INTEGER,
    PRIMARY KEY (symbol, trade_id)
);
CREATE INDEX IF NOT EXISTS idx_trades_ts
    ON trades (symbol, ts DESC);
