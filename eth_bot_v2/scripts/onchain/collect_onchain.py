import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.database.sqlite import get_connection

URL = "https://api.coingecko.com/api/v3/coins/ethereum"

response = requests.get(
    URL,
    params={
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false"
    },
    timeout=30
)

response.raise_for_status()

coin = response.json()

market = coin["market_data"]

conn = get_connection()
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO onchain(

        coin_id,
        symbol,
        name,

        current_price,

        market_cap,
        market_cap_rank,

        fully_diluted_valuation,

        circulating_supply,
        total_supply,
        max_supply,

        total_volume,

        high_24h,
        low_24h,

        price_change_24h,
        price_change_percentage_24h,

        market_cap_change_24h,
        market_cap_change_percentage_24h,

        ath,
        ath_date,

        atl,
        atl_date,

        last_updated

    )

    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,
    (

        coin["id"],
        coin["symbol"],
        coin["name"],

        market["current_price"]["usd"],

        market["market_cap"]["usd"],
        coin["market_cap_rank"],

        market["fully_diluted_valuation"]["usd"],

        market["circulating_supply"],
        market["total_supply"],
        market["max_supply"],

        market["total_volume"]["usd"],

        market["high_24h"]["usd"],
        market["low_24h"]["usd"],

        market["price_change_24h"],
        market["price_change_percentage_24h"],

        market["market_cap_change_24h"],
        market["market_cap_change_percentage_24h"],

        market["ath"]["usd"],
        market["ath_date"]["usd"],

        market["atl"]["usd"],
        market["atl_date"]["usd"],

        coin["last_updated"]

    )
)

conn.commit()

print("="*60)
print("ONCHAIN DATA SAVED")
print("="*60)

conn.close()