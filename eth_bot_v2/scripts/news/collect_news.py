import sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.database.sqlite import get_connection
from config.api.cryptopanic import (
    BASE_URL,
    API_KEY,
    DEFAULT_CURRENCY,
)

params = {
    "auth_token": API_KEY,
    "currencies": DEFAULT_CURRENCY,
    "kind": "news",
    "public": "true"
}

response = requests.get(
    BASE_URL,
    params=params,
    timeout=30
)

response.raise_for_status()

articles = response.json()["results"]

print(f"Downloaded {len(articles)} news articles")

conn = get_connection()
cursor = conn.cursor()

saved = 0

for article in articles:

    source = ""

    if article.get("source"):
        source = article["source"].get("title", "")

    cursor.execute(
        """
        INSERT OR IGNORE INTO news(

            source,
            author,
            title,
            description,
            content,
            url,
            image_url,
            published_at,
            language

        )

        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (

            source,
            article.get("author"),
            article.get("title"),
            article.get("description"),
            None,
            article.get("url"),
            article.get("image"),
            article.get("published_at"),
            "en"

        )
    )

    saved += cursor.rowcount

conn.commit()

print("=" * 60)
print("NEWS SAVED")
print("=" * 60)
print("Downloaded :", len(articles))
print("Inserted   :", saved)

conn.close()