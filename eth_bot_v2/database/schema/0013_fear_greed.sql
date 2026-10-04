-- Fear & Greed index.
CREATE TABLE IF NOT EXISTS fear_greed (
    ts    INTEGER PRIMARY KEY,
    value INTEGER NOT NULL,
    label TEXT
);
