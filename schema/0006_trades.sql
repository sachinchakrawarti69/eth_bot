CREATE TABLE IF NOT EXISTS trades (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    symbol TEXT NOT NULL,

    trade_id INTEGER NOT NULL,

    price REAL NOT NULL,

    quantity REAL NOT NULL,

    quote_quantity REAL,

    is_buyer_maker INTEGER NOT NULL,

    trade_time INTEGER NOT NULL,

    trade_datetime TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_trade
ON trades(exchange, symbol, trade_id);