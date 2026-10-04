# database/

- `market.db` â€” live SQLite database
- `init_db.py` â€” applies every file in `schema/`
- `show.py` â€” quick table inspector
- `schema/` â€” numbered migration files, one table each
- `config/api/binance.py` â€” Binance REST client (`get_klines`)

## Commands

    python database\init_db.py            # apply schema
    python database\show.py               # list tables + row counts
    python database\show.py ohlcv         # preview 5 rows

## Conventions

- One table per file
- Filenames: `NNNN_name.sql`, zero-padded, sequential
- Always `CREATE TABLE IF NOT EXISTS`
- Never `DROP` or `DELETE` in a schema file
- Timestamps: INTEGER, ms since epoch, UTC
- Prices / quantities: REAL
- IDs: TEXT or INTEGER
- Primary keys include a time column where possible (for UPSERT)

## Adding a new table

1. Create `schema/0014_whatever.sql`
2. `python database\init_db.py` â€” applies it and records it in `_schema_version`
3. Write the collector that inserts into it
