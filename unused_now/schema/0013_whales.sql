CREATE TABLE IF NOT EXISTS whales (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    tx_hash TEXT UNIQUE,

    block_number INTEGER,

    block_timestamp TEXT,

    from_address TEXT,

    to_address TEXT,

    value_eth REAL,

    gas_price REAL,

    gas_used REAL,

    transaction_fee REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_whales_time
ON whales(block_timestamp);

CREATE INDEX IF NOT EXISTS idx_whales_value
ON whales(value_eth);