"""Fix ETH 1h: delete incomplete rows and refetch 2 years."""
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "database" / "market.db"

print("DB path:", DB)
print("exists :", DB.exists())

conn = sqlite3.connect(DB)

before = conn.execute(
    "SELECT COUNT(*) FROM ohlcv WHERE symbol=? AND timeframe=?",
    ("ETHUSDT", "1h")).fetchone()[0]
print("before :", before)

cur = conn.execute(
    "DELETE FROM ohlcv WHERE symbol=? AND timeframe=?",
    ("ETHUSDT", "1h"))
conn.commit()
print("deleted:", cur.rowcount)

after = conn.execute(
    "SELECT COUNT(*) FROM ohlcv WHERE symbol=? AND timeframe=?",
    ("ETHUSDT", "1h")).fetchone()[0]
print("after  :", after)
conn.close()

if after != 0:
    print()
    print("ERROR: rows did not get deleted. Aborting refetch.")
    sys.exit(1)

print()
print("=" * 60)
print("  refetching ETH 1h (2 years)")
print("=" * 60)
rc = subprocess.call([sys.executable, "-m", "scripts_python.update_multi",
                      "--symbols", "ETHUSDT", "--timeframes", "1h"])

print()
print("final check:")
conn = sqlite3.connect(DB)
rows = conn.execute(
    "SELECT symbol, timeframe, COUNT(*) FROM ohlcv "
    "GROUP BY symbol, timeframe ORDER BY symbol, timeframe").fetchall()
for r in rows:
    print(" ", r)
conn.close()

sys.exit(rc)