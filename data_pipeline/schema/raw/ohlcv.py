"""
Raw OHLCV Schema

Supported timeframes:
- 1m
- 3m
- 5m
- 15m
- 30m
- 1h
- 2h
- 4h
- 6h
- 8h
- 12h
- 1d
"""

from dataclasses import dataclass
from datetime import datetime


SUPPORTED_TIMEFRAMES = {
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
}


@dataclass
class OHLCVSchema:
    exchange: str
    symbol: str
    timeframe: str

    open_time: datetime
    close_time: datetime

    open: float
    high: float
    low: float
    close: float

    volume: float

    quote_volume: float

    number_of_trades: int

    taker_buy_base_volume: float

    taker_buy_quote_volume: float

    def validate(self):

        if self.timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValueError(
                f"Unsupported timeframe: {self.timeframe}"
            )

        if self.high < self.low:
            raise ValueError("High price cannot be below Low.")

        if self.high < self.open:
            raise ValueError("High must be >= Open.")

        if self.high < self.close:
            raise ValueError("High must be >= Close.")

        if self.low > self.open:
            raise ValueError("Low must be <= Open.")

        if self.low > self.close:
            raise ValueError("Low must be <= Close.")

        if self.volume < 0:
            raise ValueError("Volume cannot be negative.")