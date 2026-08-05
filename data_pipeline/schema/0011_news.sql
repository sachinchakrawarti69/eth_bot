CREATE TABLE IF NOT EXISTS news (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source TEXT NOT NULL,

    author TEXT,

    title TEXT NOT NULL,

    description TEXT,

    content TEXT,

    url TEXT UNIQUE,

    image_url TEXT,

    published_at TEXT,

    language TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_source
ON news(source);

CREATE INDEX IF NOT EXISTS idx_news_published
ON news(published_at);