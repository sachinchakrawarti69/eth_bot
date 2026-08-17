CREATE TABLE IF NOT EXISTS funding_rate (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    symbol TEXT NOT NULL,

    funding_rate REAL NOT NULL,

    funding_time INTEGER NOT NULL,

    funding_datetime TEXT NOT NULL,

    mark_price REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_funding_rate
ON funding_rate(symbol, funding_time);