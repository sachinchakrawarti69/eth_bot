import sqlite3
import requests
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.api.binance import (
    get_open_interest_url,
    DEFAULT_SYMBOL,
)

# ============================================================
# Database
# ============================================================

DB_PATH = ROOT / "storage" / "database" / "ETH.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# ============================================================
# Download Open Interest
# ============================================================

params = {
    "symbol": DEFAULT_SYMBOL
}

response = requests.get(
    get_open_interest_url(),
    params=params,
    timeout=30
)

response.raise_for_status()

data = response.json()

# ============================================================
# Save
# ============================================================

cursor.execute(
    """
    INSERT INTO open_interest(
        exchange,
        symbol,
        open_interest
    )
    VALUES(?,?,?)
    """,
    (
        "Binance",
        data["symbol"],
        float(data["openInterest"])
    )
)

connection.commit()

print("=" * 50)
print("OPEN INTEREST SAVED")
print("=" * 50)

print(f"Exchange       : Binance")
print(f"Symbol         : {data['symbol']}")
print(f"Open Interest  : {data['openInterest']}")

connection.close()