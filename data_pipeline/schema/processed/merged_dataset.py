"""
Merged Dataset Schema

Defines the final AI-ready dataset produced after merging all processed
data sources in the ETH Bot Data Pipeline.

This dataset is the primary input for:

- LSTM
- GRU
- Transformer
- Temporal Fusion Transformer
- TCN
- XGBoost
- LightGBM
- CatBoost

All processed schemas are synchronized by timestamp before merging.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_MARKETS = {
    "spot",
    "futures",
    "coinm",
}


SUPPORTED_TIMEFRAMES = {
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
}


@dataclass
class MergedDatasetSchema:
    """
    Final AI-ready merged dataset schema.
    """

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str

    exchange: str

    market: str

    timeframe: str

    timestamp: datetime

    # ==========================================================
    # Processed Market Data
    # ==========================================================

    open: float

    high: float

    low: float

    close: float

    volume: float

    quote_volume: Optional[float] = None

    number_of_trades: Optional[int] = None

    # ==========================================================
    # Processed Derivatives
    # ==========================================================

    open_interest: Optional[float] = None

    funding_rate: Optional[float] = None

    long_short_ratio: Optional[float] = None

    liquidation_volume: Optional[float] = None

    implied_volatility: Optional[float] = None

    put_call_ratio: Optional[float] = None

    # ==========================================================
    # Processed Sentiment
    # ==========================================================

    news_sentiment: Optional[float] = None

    social_sentiment: Optional[float] = None

    market_sentiment: Optional[float] = None

    fear_greed_index: Optional[int] = None

    overall_sentiment_score: Optional[float] = None

    # ==========================================================
    # Processed On-Chain
    # ==========================================================

    active_addresses: Optional[int] = None

    exchange_balance: Optional[float] = None

    exchange_inflow: Optional[float] = None

    exchange_outflow: Optional[float] = None

    whale_volume: Optional[float] = None

    staking_ratio: Optional[float] = None

    # ==========================================================
    # Dataset Metadata
    # ==========================================================

    processed_at: datetime

    dataset_version: str

    source_records: int

    quality_score: float

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if not self.symbol:
            raise ValueError("Symbol is required.")

        if self.market not in SUPPORTED_MARKETS:
            raise ValueError("Unsupported market.")

        if self.timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValueError("Unsupported timeframe.")

        if self.open <= 0:
            raise ValueError("Invalid open price.")

        if self.high <= 0:
            raise ValueError("Invalid high price.")

        if self.low <= 0:
            raise ValueError("Invalid low price.")

        if self.close <= 0:
            raise ValueError("Invalid close price.")

        if self.volume < 0:
            raise ValueError("Invalid volume.")

        if not (0 <= self.quality_score <= 1):
            raise ValueError("Quality score must be between 0 and 1.")

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def bullish(self):
        return self.close > self.open

    @property
    def bearish(self):
        return self.close < self.open

    @property
    def candle_range(self):
        return self.high - self.low

    @property
    def candle_body(self):
        return abs(self.close - self.open)

    @property
    def exchange_netflow(self):
        if (
            self.exchange_inflow is None or
            self.exchange_outflow is None
        ):
            return None

        return (
            self.exchange_inflow -
            self.exchange_outflow
        )

    @property
    def market_is_bullish(self):
        return (
            self.overall_sentiment_score is not None
            and self.overall_sentiment_score > 0
        )

    @property
    def market_is_bearish(self):
        return (
            self.overall_sentiment_score is not None
            and self.overall_sentiment_score < 0
        )