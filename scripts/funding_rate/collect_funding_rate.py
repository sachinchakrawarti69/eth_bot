import sqlite3
import requests
import sys
from pathlib import Path
from datetime import datetime, timezone

# ============================================================
# Project Root
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.api.binance import (
    get_funding_rate_url,
    DEFAULT_SYMBOL,
)

# ============================================================
# Database
# ============================================================

DB_PATH = ROOT / "storage" / "database" / "ETH.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# ============================================================
# Download Funding Rate
# ============================================================

params = {
    "symbol": DEFAULT_SYMBOL,
    "limit": 1
}

response = requests.get(
    get_funding_rate_url(),
    params=params,
    timeout=30
)

response.raise_for_status()

result = response.json()

if not result:
    print("No funding rate data received.")
    connection.close()
    exit()

data = result[0]

# ============================================================
# Extract Data
# ============================================================

exchange = "Binance"

symbol = data["symbol"]

funding_rate = float(data["fundingRate"])

funding_time = int(data["fundingTime"])

funding_datetime = datetime.fromtimestamp(
    funding_time / 1000,
    tz=timezone.utc
).strftime("%Y-%m-%d %H:%M:%S")

mark_price = float(data.get("markPrice", 0))

# ============================================================
# Save to Database
# ============================================================

cursor.execute(
    """
    INSERT INTO funding_rate(

        exchange,
        symbol,
        funding_rate,
        funding_time,
        funding_datetime,
        mark_price

    )
    VALUES(?,?,?,?,?,?)
    """,
    (
        exchange,
        symbol,
        funding_rate,
        funding_time,
        funding_datetime,
        mark_price
    )
)

connection.commit()

# ============================================================
# Output
# ============================================================

print("=" * 60)
print("FUNDING RATE SAVED SUCCESSFULLY")
print("=" * 60)

print(f"Exchange          : {exchange}")
print(f"Symbol            : {symbol}")
print(f"Funding Rate      : {funding_rate}")
print(f"Funding Time      : {funding_datetime}")
print(f"Mark Price        : {mark_price}")

print("=" * 60)

connection.close()