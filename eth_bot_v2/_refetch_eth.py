"""Force-refetch ETH open_interest and funding from scratch."""
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "database" / "market.db"

conn = sqlite3.connect(DB)

print("=" * 60)
print("  BEFORE")
print("=" * 60)
for t in ("open_interest", "funding_rate"):
    n = conn.execute(f"SELECT COUNT(*) FROM {t} WHERE symbol='ETHUSDT'").fetchone()[0]
    print(f"  {t:<20} ETHUSDT  {n:>6}")

print()
print("deleting ETH rows from those two tables...")
conn.execute("DELETE FROM open_interest WHERE symbol='ETHUSDT'")
conn.execute("DELETE FROM funding_rate WHERE symbol='ETHUSDT'")
conn.commit()

print()
print("=" * 60)
print("  AFTER DELETE")
print("=" * 60)
for t in ("open_interest", "funding_rate"):
    n = conn.execute(f"SELECT COUNT(*) FROM {t} WHERE symbol='ETHUSDT'").fetchone()[0]
    print(f"  {t:<20} ETHUSDT  {n:>6}")

conn.close()

print()
print("=" * 60)
print("  REFETCHING ETH")
print("=" * 60)
rc1 = subprocess.call([sys.executable, "-m", "scripts_python.fetch_oi",
                       "--symbols", "ETHUSDT"])
rc2 = subprocess.call([sys.executable, "-m", "scripts_python.fetch_funding",
                       "--symbols", "ETHUSDT"])

print()
print("=" * 60)
print("  FINAL")
print("=" * 60)
conn = sqlite3.connect(DB)
for t in ("open_interest", "long_short_ratio", "taker_volume", "funding_rate"):
    rows = conn.execute(
        f"SELECT symbol, COUNT(*) FROM {t} GROUP BY symbol ORDER BY symbol"
    ).fetchall()
    for sym, n in rows:
        print(f"  {t:<20} {sym:<10} {n:>6}")
conn.close()

sys.exit(rc1 or rc2)