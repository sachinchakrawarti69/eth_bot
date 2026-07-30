import sqlite3
from pathlib import Path

import pandas as pd


# ==========================================================
# Project Paths
# ==========================================================

ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = ROOT / "storage" / "database" / "ETH.db"


# ==========================================================
# Database Connection
# ==========================================================

def get_connection():
    """
    Create SQLite connection.
    """
    return sqlite3.connect(DATABASE_PATH)


# ==========================================================
# Generic Loader
# ==========================================================

def load_table(table_name: str) -> pd.DataFrame:
    """
    Load any table from ETH.db.
    """

    conn = get_connection()

    query = f"SELECT * FROM {table_name}"

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==========================================================
# Individual Loaders
# ==========================================================

def load_ohlcv():
    return load_table("ohlcv")


def load_orderbook():
    return load_table("orderbook")


def load_trades():
    return load_table("trades")


def load_funding_rate():
    return load_table("funding_rate")


def load_open_interest():
    return load_table("open_interest")


def load_option_chain():
    return load_table("option_chain")


def load_greeks():
    return load_table("greeks")


def load_implied_volatility():
    return load_table("implied_volatility")


def load_news():
    return load_table("news")


def load_onchain():
    return load_table("onchain")


def load_whales():
    return load_table("whales")


def load_fear_greed():
    return load_table("fear_greed")


# ==========================================================
# Dataset Summary
# ==========================================================

def dataset_summary():
    """
    Print row count for all datasets.
    """

    tables = [
        "ohlcv",
        "orderbook",
        "trades",
        "funding_rate",
        "open_interest",
        "option_chain",
        "greeks",
        "implied_volatility",
        "news",
        "onchain",
        "whales",
        "fear_greed",
    ]

    print("=" * 60)
    print("ETH DATABASE SUMMARY")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor()

    for table in tables:

        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")

            count = cursor.fetchone()[0]

            print(f"{table:<22} {count}")

        except Exception:

            print(f"{table:<22} Not Found")

    conn.close()


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    dataset_summary()

    print()

    df = load_ohlcv()

    print(df.head())

    print()

    print(df.shape)

    print()

    print(df.info())