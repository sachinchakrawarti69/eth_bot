"""
Processed Market Data Schema

Defines the canonical schema for processed market data used by the
ETH Bot AI Trading System.

This schema is generated after:

- Raw data validation
- Data cleaning
- Missing value handling
- Timestamp alignment
- Duplicate removal
- Timeframe aggregation
- Exchange normalization

Unlike raw schemas, processed schemas are standardized, quality checked,
and ready for technical indicator calculation and feature engineering.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_TIMEFRAMES = {
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
    "1w",
}

SUPPORTED_MARKETS = {
    "spot",
    "futures",
    "coinm",
}

SUPPORTED_EXCHANGES = {
    "binance",
    "bybit",
    "okx",
}


@dataclass
class ProcessedMarketDataSchema:
    """
    Canonical processed market data schema.
    """

    # ==========================================================
    # Asset Information
    # ==========================================================

    exchange: str

    symbol: str

    market: str

    timeframe: str

    # ==========================================================
    # Candle Information
    # ==========================================================

    open_time: datetime

    close_time: datetime

    open: float

    high: float

    low: float

    close: float

    volume: float

    quote_volume: Optional[float] = None

    number_of_trades: Optional[int] = None

    taker_buy_base_volume: Optional[float] = None

    taker_buy_quote_volume: Optional[float] = None

    # ==========================================================
    # Processing Metadata
    # ==========================================================

    processed_at: datetime

    source_records: int

    data_quality_score: float

    missing_values_filled: int = 0

    duplicate_records_removed: int = 0

    anomalies_detected: int = 0

    # ==========================================================
    # Quality Flags
    # ==========================================================

    is_complete: bool = True

    is_validated: bool = True

    is_interpolated: bool = False

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if self.exchange not in SUPPORTED_EXCHANGES:
            raise ValueError(
                f"Unsupported exchange: {self.exchange}"
            )

        if not self.symbol:
            raise ValueError(
                "Symbol is required."
            )

        if self.market not in SUPPORTED_MARKETS:
            raise ValueError(
                f"Unsupported market: {self.market}"
            )

        if self.timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValueError(
                f"Unsupported timeframe: {self.timeframe}"
            )

        if self.open <= 0:
            raise ValueError("Open price must be positive.")

        if self.high <= 0:
            raise ValueError("High price must be positive.")

        if self.low <= 0:
            raise ValueError("Low price must be positive.")

        if self.close <= 0:
            raise ValueError("Close price must be positive.")

        if self.high < self.low:
            raise ValueError(
                "High price cannot be less than low price."
            )

        if self.high < max(self.open, self.close):
            raise ValueError(
                "High price is invalid."
            )

        if self.low > min(self.open, self.close):
            raise ValueError(
                "Low price is invalid."
            )

        if self.volume < 0:
            raise ValueError(
                "Volume cannot be negative."
            )

        if not (0 <= self.data_quality_score <= 1):
            raise ValueError(
                "Quality score must be between 0 and 1."
            )

        if self.source_records <= 0:
            raise ValueError(
                "Source records must be greater than zero."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def candle_range(self) -> float:
        return self.high - self.low

    @property
    def candle_body(self) -> float:
        return abs(self.close - self.open)

    @property
    def bullish(self) -> bool:
        return self.close > self.open

    @property
    def bearish(self) -> bool:
        return self.close < self.open

    @property
    def doji(self) -> bool:
        return self.open == self.close

    @property
    def typical_price(self) -> float:
        return (
            self.high +
            self.low +
            self.close
        ) / 3

    @property
    def hl2(self) -> float:
        return (
            self.high +
            self.low
        ) / 2

    @property
    def ohlc4(self) -> float:
        return (
            self.open +
            self.high +
            self.low +
            self.close
        ) / 4

    @property
    def quality_percent(self) -> float:
        return self.data_quality_score * 100