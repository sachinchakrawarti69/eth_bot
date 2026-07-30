import sqlite3
import requests
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.api.binance import (
    BASE_URL,
    ORDERBOOK_ENDPOINT,
    DEFAULT_SYMBOL,
    DEFAULT_ORDERBOOK_LIMIT,
)

# ============================================================
# Database
# ============================================================

DB_PATH = ROOT / "storage" / "database" / "ETH.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# ============================================================
# Download Order Book
# ============================================================

url = BASE_URL + ORDERBOOK_ENDPOINT

params = {
    "symbol": DEFAULT_SYMBOL,
    "limit": DEFAULT_ORDERBOOK_LIMIT,
}

response = requests.get(url, params=params)
response.raise_for_status()

data = response.json()

snapshot_time = int(time.time() * 1000)

print(f"Downloaded {len(data['bids'])} bids")
print(f"Downloaded {len(data['asks'])} asks")

# ============================================================
# Save Bids
# ============================================================

for bid in data["bids"]:

    cursor.execute(
        """
        INSERT INTO orderbook(
            exchange,
            symbol,
            side,
            price,
            quantity,
            snapshot_time
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            "Binance",
            DEFAULT_SYMBOL,
            "BID",
            float(bid[0]),
            float(bid[1]),
            snapshot_time,
        ),
    )

# ============================================================
# Save Asks
# ============================================================

for ask in data["asks"]:

    cursor.execute(
        """
        INSERT INTO orderbook(
            exchange,
            symbol,
            side,
            price,
            quantity,
            snapshot_time
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            "Binance",
            DEFAULT_SYMBOL,
            "ASK",
            float(ask[0]),
            float(ask[1]),
            snapshot_time,
        ),
    )

connection.commit()

print("Order book saved successfully!")

connection.close()