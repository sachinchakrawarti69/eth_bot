CREATE TABLE IF NOT EXISTS ohlcv (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    symbol TEXT NOT NULL,

    interval TEXT NOT NULL,

    open_time INTEGER NOT NULL,

    open REAL NOT NULL,

    high REAL NOT NULL,

    low REAL NOT NULL,

    close REAL NOT NULL,

    volume REAL NOT NULL,

    close_time INTEGER NOT NULL,

    quote_asset_volume REAL,

    number_of_trades INTEGER,

    taker_buy_base_volume REAL,

    taker_buy_quote_volume REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_symbol_interval_time
ON ohlcv(symbol, interval, open_time);