CREATE TABLE IF NOT EXISTS implied_volatility (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    instrument_name TEXT NOT NULL,

    option_type TEXT,

    strike REAL,

    expiration_timestamp INTEGER,

    expiration_datetime TEXT,

    mark_iv REAL,

    bid_iv REAL,

    ask_iv REAL,

    underlying_price REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_iv
ON implied_volatility(instrument_name);