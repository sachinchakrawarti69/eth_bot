"""Read market.db into pandas."""
import sqlite3
from pathlib import Path
import pandas as pd

DB = Path(__file__).resolve().parents[1] / "database" / "market.db"


def load_ohlcv(symbol: str = "ETHUSDT", timeframe: str = "1d") -> pd.DataFrame:
    with sqlite3.connect(DB) as c:
        df = pd.read_sql_query(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlcv WHERE symbol=? AND timeframe=? ORDER BY open_time",
            c, params=(symbol, timeframe))
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    return df.drop(columns=["open_time"]).set_index("date")


def load_table(table: str) -> pd.DataFrame:
    with sqlite3.connect(DB) as c:
        return pd.read_sql_query(f"SELECT * FROM {table}", c)
