CREATE TABLE IF NOT EXISTS liquidations (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    symbol TEXT NOT NULL,

    order_id INTEGER,

    side TEXT,

    order_type TEXT,

    time_in_force TEXT,

    original_quantity REAL,

    price REAL,

    average_price REAL,

    order_status TEXT,

    last_filled_quantity REAL,

    accumulated_filled_quantity REAL,

    trade_time INTEGER,

    trade_datetime TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_liquidation
ON liquidations(exchange, symbol, order_id);