import sys
from pathlib import Path
from datetime import datetime, timezone

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.database.sqlite import get_connection
from config.api.binance import get_force_orders_url

SYMBOL = "ETHUSD_PERP"

conn = get_connection()
cursor = conn.cursor()

response = requests.get(
    get_force_orders_url(),
    params={
        "symbol": SYMBOL,
        "limit": 100
    },
    timeout=30
)

response.raise_for_status()

orders = response.json()

print(f"Downloaded {len(orders)} liquidation records")

saved = 0

for order in orders:

    trade_time = int(order["time"])

    trade_datetime = datetime.fromtimestamp(
        trade_time / 1000,
        tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT OR IGNORE INTO liquidations(

            exchange,
            symbol,
            order_id,
            side,
            order_type,
            time_in_force,
            original_quantity,
            price,
            average_price,
            order_status,
            last_filled_quantity,
            accumulated_filled_quantity,
            trade_time,
            trade_datetime

        )

        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Binance",
            order["symbol"],
            order["orderId"],
            order["side"],
            order["type"],
            order["timeInForce"],
            float(order["origQty"]),
            float(order["price"]),
            float(order["averagePrice"]),
            order["status"],
            float(order["lastFilledQty"]),
            float(order["executedQty"]),
            trade_time,
            trade_datetime
        )
    )

    saved += cursor.rowcount

conn.commit()

print("=" * 60)
print("LIQUIDATIONS SAVED")
print("=" * 60)
print("Downloaded :", len(orders))
print("Inserted   :", saved)

conn.close()