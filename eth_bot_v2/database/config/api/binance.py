"""Binance API - klines endpoint only."""

import requests

BASE_URL = "https://api.binance.com"


def get_klines(symbol: str, interval: str = "1d",
               start_ms: int | None = None, limit: int = 1000) -> list:
    """Fetch klines from Binance."""
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_ms is not None:
        params["startTime"] = int(start_ms)

    r = requests.get(f"{BASE_URL}/api/v3/klines", params=params, timeout=10)
    r.raise_for_status()
    return r.json()
