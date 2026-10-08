"""Apply every SQL file in database/schema/options/ to options.db."""

import sqlite3
import sys
import time
from pathlib import Path

DB_PATH    = Path(__file__).resolve().parent / "options.db"
SCHEMA_DIR = Path(__file__).resolve().parent / "schema" / "options"


def init() -> int:
    if not SCHEMA_DIR.exists():
        print(f"schema dir missing: {SCHEMA_DIR}")
        return 1

    files = sorted(SCHEMA_DIR.glob("*.sql"))
    if not files:
        print(f"no .sql files in {SCHEMA_DIR}")
        return 1

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _schema_version ("
            "  filename   TEXT PRIMARY KEY,"
            "  applied_at INTEGER NOT NULL)"
        )
        conn.commit()

        for f in files:
            print(f"applying {f.name}")
            conn.executescript(f.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT OR IGNORE INTO _schema_version (filename, applied_at) "
                "VALUES (?, ?)", (f.name, int(time.time())))
            conn.commit()

        print(f"\ntables in {DB_PATH.name}:")
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for t in tables:
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:<22} rows={n}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(init())
