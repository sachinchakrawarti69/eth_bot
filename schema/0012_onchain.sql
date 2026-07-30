CREATE TABLE IF NOT EXISTS onchain (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    coin_id TEXT NOT NULL,

    symbol TEXT NOT NULL,

    name TEXT NOT NULL,

    current_price REAL,

    market_cap REAL,

    market_cap_rank INTEGER,

    fully_diluted_valuation REAL,

    circulating_supply REAL,

    total_supply REAL,

    max_supply REAL,

    total_volume REAL,

    high_24h REAL,

    low_24h REAL,

    price_change_24h REAL,

    price_change_percentage_24h REAL,

    market_cap_change_24h REAL,

    market_cap_change_percentage_24h REAL,

    ath REAL,

    ath_date TEXT,

    atl REAL,

    atl_date TEXT,

    last_updated TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);