import sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.database.sqlite import get_connection
from config.api.deribit import get_order_book_url

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT
    instrument_name,
    option_type,
    strike,
    expiration_timestamp,
    expiration_datetime
FROM option_chain
""")

contracts = cursor.fetchall()

print(f"Found {len(contracts)} contracts")

saved = 0

for row in contracts:

    instrument = row[0]

    response = requests.get(
        get_order_book_url(),
        params={
            "instrument_name": instrument
        },
        timeout=30
    )

    if response.status_code != 200:
        continue

    result = response.json().get("result")

    if not result:
        continue

    cursor.execute(
        """
        INSERT OR REPLACE INTO implied_volatility(

            exchange,
            instrument_name,
            option_type,
            strike,
            expiration_timestamp,
            expiration_datetime,
            mark_iv,
            bid_iv,
            ask_iv,
            underlying_price

        )

        VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (

            "Deribit",

            row[0],
            row[1],
            row[2],
            row[3],
            row[4],

            result.get("mark_iv"),
            result.get("bid_iv"),
            result.get("ask_iv"),
            result.get("underlying_price")

        )
    )

    saved += 1

conn.commit()

print("=" * 60)
print("IMPLIED VOLATILITY SAVED")
print("=" * 60)
print("Saved:", saved)

conn.close()