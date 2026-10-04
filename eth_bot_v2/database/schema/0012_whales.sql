-- Large wallet movements.
CREATE TABLE IF NOT EXISTS whales (
    tx_hash   TEXT    NOT NULL,
    ts        INTEGER NOT NULL,
    from_addr TEXT,
    to_addr   TEXT,
    amount    REAL    NOT NULL,
    token     TEXT    NOT NULL,
    PRIMARY KEY (tx_hash, token)
);
CREATE INDEX IF NOT EXISTS idx_whales_ts
    ON whales (ts DESC);
