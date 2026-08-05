CREATE TABLE IF NOT EXISTS fear_greed (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    value INTEGER NOT NULL,

    value_classification TEXT NOT NULL,

    timestamp INTEGER NOT NULL,

    datetime TEXT NOT NULL,

    time_until_update INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fear_greed_timestamp
ON fear_greed(timestamp);