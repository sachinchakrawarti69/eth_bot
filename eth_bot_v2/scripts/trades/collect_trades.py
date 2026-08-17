import sqlite3
import requests
import sys

from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.api.binance import (
    get_trades_url,
    DEFAULT_SYMBOL,
    DEFAULT_TRADES_LIMIT,
)

# ============================================================
# Database
# ============================================================

DB_PATH = ROOT / "storage" / "database" / "ETH.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# ============================================================
# Download Trades
# ============================================================

params = {
    "symbol": DEFAULT_SYMBOL,
    "limit": DEFAULT_TRADES_LIMIT
}

response = requests.get(
    get_trades_url(),
    params=params,
    timeout=30
)

response.raise_for_status()

trades = response.json()

print(f"Downloaded {len(trades)} trades")

# ============================================================
# Save
# ============================================================

saved = 0

for trade in trades:

    trade_time = int(trade["time"])

    trade_datetime = datetime.fromtimestamp(
        trade_time / 1000,
        tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S")

    quote_quantity = (
        float(trade["price"]) *
        float(trade["qty"])
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO trades(

            exchange,
            symbol,
            trade_id,
            price,
            quantity,
            quote_quantity,
            is_buyer_maker,
            trade_time,
            trade_datetime

        )
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            "Binance",
            DEFAULT_SYMBOL,
            trade["id"],
            float(trade["price"]),
            float(trade["qty"]),
            quote_quantity,
            int(trade["isBuyerMaker"]),
            trade_time,
            trade_datetime
        )
    )

    saved += cursor.rowcount

connection.commit()

print("=" * 60)
print("TRADES SAVED")
print("=" * 60)
print("Downloaded :", len(trades))
print("Inserted   :", saved)

connection.close()