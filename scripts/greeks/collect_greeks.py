import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.database.sqlite import get_connection
from config.api.deribit import get_order_book_url

# ============================================================
# Database
# ============================================================

conn = get_connection()
cursor = conn.cursor()

# ============================================================
# Read option contracts
# ============================================================

cursor.execute("""
SELECT instrument_name
FROM option_chain
ORDER BY instrument_name
""")

contracts = cursor.fetchall()

print(f"Found {len(contracts)} contracts")

saved = 0
skipped = 0
errors = 0

# ============================================================
# Download Greeks
# ============================================================

for row in contracts:

    instrument = row[0]

    try:

        response = requests.get(
            get_order_book_url(),
            params={
                "instrument_name": instrument
            },
            timeout=30
        )

        response.raise_for_status()

        result = response.json().get("result")

        if result is None:
            skipped += 1
            print(f"Skipped: {instrument} (No result)")
            continue

        greeks = result.get("greeks")

        if not greeks:
            skipped += 1
            print(f"Skipped: {instrument} (No Greeks)")
            continue

        cursor.execute(
            """
            INSERT OR REPLACE INTO greeks(

                exchange,
                instrument_name,
                delta,
                gamma,
                theta,
                vega,
                rho,
                mark_iv,
                bid_iv,
                ask_iv,
                underlying_price

            )

            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Deribit",
                instrument,
                greeks.get("delta"),
                greeks.get("gamma"),
                greeks.get("theta"),
                greeks.get("vega"),
                greeks.get("rho"),
                result.get("mark_iv"),
                result.get("bid_iv"),
                result.get("ask_iv"),
                result.get("underlying_price")
            )
        )

        saved += 1

        if saved % 50 == 0:
            conn.commit()
            print(f"Saved {saved} contracts...")

    except Exception as e:
        errors += 1
        print(f"Error: {instrument}")
        print(e)

# ============================================================
# Finish
# ============================================================

conn.commit()

cursor.execute("SELECT COUNT(*) FROM greeks")
rows = cursor.fetchone()[0]

print("\n" + "=" * 60)
print("GREEKS COLLECTION COMPLETE")
print("=" * 60)
print(f"Contracts Found : {len(contracts)}")
print(f"Saved           : {saved}")
print(f"Skipped         : {skipped}")
print(f"Errors          : {errors}")
print(f"Rows in DB      : {rows}")

conn.close()