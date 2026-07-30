CREATE TABLE IF NOT EXISTS orderbook (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    symbol TEXT NOT NULL,

    side TEXT NOT NULL,

    price REAL NOT NULL,

    quantity REAL NOT NULL,

    snapshot_time INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orderbook
ON orderbook(symbol, snapshot_time);