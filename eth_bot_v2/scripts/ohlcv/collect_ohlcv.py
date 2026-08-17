import sqlite3
import requests
from pathlib import Path

from config.api.binance import (
    get_klines_url,
    DEFAULT_SYMBOL,
    DEFAULT_INTERVAL,
    DEFAULT_LIMIT,
)

# ============================================================
# Database
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "storage" / "database" / "ETH.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# ============================================================
# Download Data
# ============================================================

params = {
    "symbol": DEFAULT_SYMBOL,
    "interval": DEFAULT_INTERVAL,
    "limit": DEFAULT_LIMIT,
}

response = requests.get(get_klines_url(), params=params)
response.raise_for_status()

candles = response.json()

print(f"Downloaded {len(candles)} candles")

# ============================================================
# Save to SQLite
# ============================================================

for candle in candles:

    cursor.execute(
        """
        INSERT INTO ohlcv(
            exchange,
            symbol,
            interval,
            open_time,
            open,
            high,
            low,
            close,
            volume,
            close_time,
            quote_asset_volume,
            number_of_trades,
            taker_buy_base_volume,
            taker_buy_quote_volume
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Binance",
            DEFAULT_SYMBOL,
            DEFAULT_INTERVAL,

            candle[0],

            float(candle[1]),
            float(candle[2]),
            float(candle[3]),
            float(candle[4]),

            float(candle[5]),

            candle[6],

            float(candle[7]),

            candle[8],

            float(candle[9]),

            float(candle[10]),
        ),
    )

connection.commit()

print("Saved successfully!")

connection.close()