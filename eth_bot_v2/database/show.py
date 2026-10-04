"""Quick DB inspector.   python database/show.py [table]"""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parent / "market.db"


def tables(conn):
    print(f"DB: {DB}\n")
    for (t,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<22} rows={n}")


def preview(conn, table, limit=5):
    cur = conn.execute(f"SELECT * FROM {table} LIMIT {limit}")
    cols = [d[0] for d in cur.description]
    print(" | ".join(cols))
    print("-" * 60)
    for row in cur.fetchall():
        print(" | ".join(str(v) for v in row))


def main():
    if not DB.exists():
        print(f"DB not found: {DB}")
        return 1
    conn = sqlite3.connect(DB)
    try:
        if len(sys.argv) > 1:
            preview(conn, sys.argv[1])
        else:
            tables(conn)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
