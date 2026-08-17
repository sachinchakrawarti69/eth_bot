import sys
from pathlib import Path
import requests
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.api.deribit import get_instruments_url
from config.database.sqlite import get_connection

# ============================================================
# Settings
# ============================================================

CURRENCY = "ETH"

# ============================================================
# Database
# ============================================================

conn = get_connection()
cursor = conn.cursor()

# ============================================================
# Download Instruments
# ============================================================

response = requests.get(
    get_instruments_url(),
    params={
        "currency": CURRENCY,
        "kind": "option",
        "expired": "false"
    },
    timeout=30
)

response.raise_for_status()

instruments = response.json()["result"]

print(f"Found {len(instruments)} option contracts")

saved = 0

for item in instruments:

    expiry = int(item["expiration_timestamp"])

    expiry_date = datetime.fromtimestamp(
        expiry / 1000,
        tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT OR REPLACE INTO option_chain(

            exchange,
            instrument_name,
            base_currency,
            option_type,
            strike,
            expiration_timestamp,
            expiration_datetime,
            bid_price,
            ask_price,
            mark_price,
            last_price,
            open_interest,
            volume,
            underlying_price

        )

        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (

            "Deribit",

            item["instrument_name"],

            item["base_currency"],

            item["option_type"],

            float(item["strike"]),

            expiry,

            expiry_date,

            None,
            None,
            None,
            None,
            None,
            None,
            None

        )
    )

    saved += 1

conn.commit()

print("=" * 60)
print("OPTION CHAIN SAVED")
print("=" * 60)
print("Contracts Found :", len(instruments))
print("Contracts Saved :", saved)

cursor.execute("SELECT COUNT(*) FROM option_chain")
print("Rows in Database:", cursor.fetchone()[0])

conn.close()