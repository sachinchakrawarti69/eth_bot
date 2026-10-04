-- Order book snapshots.
CREATE TABLE IF NOT EXISTS orderbook (
    symbol      TEXT    NOT NULL,
    ts          INTEGER NOT NULL,
    bid_price   REAL    NOT NULL,
    bid_qty     REAL    NOT NULL,
    ask_price   REAL    NOT NULL,
    ask_qty     REAL    NOT NULL,
    PRIMARY KEY (symbol, ts)
);
CREATE INDEX IF NOT EXISTS idx_orderbook_ts
    ON orderbook (symbol, ts DESC);
