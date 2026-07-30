CREATE TABLE IF NOT EXISTS open_interest (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    symbol TEXT NOT NULL,

    open_interest REAL NOT NULL,

    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_open_interest
ON open_interest(symbol, timestamp);