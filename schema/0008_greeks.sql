CREATE TABLE IF NOT EXISTS greeks (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    exchange TEXT NOT NULL,

    instrument_name TEXT NOT NULL,

    delta REAL,

    gamma REAL,

    theta REAL,

    vega REAL,

    rho REAL,

    mark_iv REAL,

    bid_iv REAL,

    ask_iv REAL,

    underlying_price REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_greeks
ON greeks(instrument_name);