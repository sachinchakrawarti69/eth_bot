import sys
from pathlib import Path
from datetime import datetime

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.database.sqlite import get_connection

URL = "https://api.alternative.me/fng/"

response = requests.get(
    URL,
    params={
        "limit": 100,
        "format": "json"
    },
    timeout=30
)

response.raise_for_status()

data = response.json()["data"]

print(f"Downloaded {len(data)} records")

conn = get_connection()
cursor = conn.cursor()

saved = 0

for row in data:

    ts = int(row["timestamp"])

    dt = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT OR IGNORE INTO fear_greed(

            value,
            value_classification,
            timestamp,
            datetime,
            time_until_update

        )

        VALUES(?,?,?,?,?)
        """,
        (
            int(row["value"]),
            row["value_classification"],
            ts,
            dt,
            row.get("time_until_update")
        )
    )

    saved += cursor.rowcount

conn.commit()

print("=" * 60)
print("FEAR & GREED SAVED")
print("=" * 60)
print("Inserted :", saved)

conn.close()