CREATE TABLE IF NOT EXISTS option_chain (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    instrument_name TEXT NOT NULL,

    base_currency TEXT NOT NULL,

    option_type TEXT NOT NULL,

    strike REAL NOT NULL,

    expiration_timestamp INTEGER NOT NULL,

    expiration_datetime TEXT NOT NULL,

    bid_price REAL,

    ask_price REAL,

    mark_price REAL,

    last_price REAL,

    open_interest REAL,

    volume REAL,

    underlying_price REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_option_chain
ON option_chain(instrument_name);