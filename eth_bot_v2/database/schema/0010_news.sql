-- News / headlines.
CREATE TABLE IF NOT EXISTS news (
    id        TEXT PRIMARY KEY,
    ts        INTEGER NOT NULL,
    source    TEXT,
    title     TEXT,
    url       TEXT,
    sentiment REAL,
    body      TEXT
);
CREATE INDEX IF NOT EXISTS idx_news_ts
    ON news (ts DESC);
