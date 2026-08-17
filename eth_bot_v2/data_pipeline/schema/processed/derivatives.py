"""
Processed Derivatives Schema

Defines the canonical processed derivatives data schema used by the
ETH Bot AI Trading System.

This schema combines validated and normalized derivatives market data
from multiple raw sources including:

- Open Interest
- Funding Rate
- Long/Short Ratio
- Liquidations
- Option Chain
- Greeks
- Implied Volatility

The processed derivatives schema is optimized for feature engineering,
quantitative research, risk analysis, and AI model training.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_EXCHANGES = {
    "binance",
    "bybit",
    "okx",
}

SUPPORTED_MARKETS = {
    "futures",
    "options",
}

SUPPORTED_TIMEFRAMES = {
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
}


@dataclass
class ProcessedDerivativesSchema:
    """
    Canonical processed derivatives schema.
    """

    # ==========================================================
    # Asset Information
    # ==========================================================

    exchange: str

    symbol: str

    market: str

    timeframe: str

    timestamp: datetime

    # ==========================================================
    # Futures Metrics
    # ==========================================================

    open_interest: Optional[float] = None

    open_interest_value_usd: Optional[float] = None

    funding_rate: Optional[float] = None

    predicted_funding_rate: Optional[float] = None

    long_short_ratio: Optional[float] = None

    top_trader_long_short_ratio: Optional[float] = None

    # ==========================================================
    # Liquidation Metrics
    # ==========================================================

    long_liquidation_volume: Optional[float] = None

    short_liquidation_volume: Optional[float] = None

    total_liquidation_volume: Optional[float] = None

    liquidation_count: Optional[int] = None

    # ==========================================================
    # Options Metrics
    # ==========================================================

    implied_volatility: Optional[float] = None

    historical_volatility: Optional[float] = None

    call_open_interest: Optional[float] = None

    put_open_interest: Optional[float] = None

    put_call_ratio: Optional[float] = None

    # ==========================================================
    # Aggregated Greeks
    # ==========================================================

    average_delta: Optional[float] = None

    average_gamma: Optional[float] = None

    average_theta: Optional[float] = None

    average_vega: Optional[float] = None

    average_rho: Optional[float] = None

    # ==========================================================
    # Quality Metadata
    # ==========================================================

    processed_at: datetime

    source_records: int

    data_quality_score: float

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if self.exchange not in SUPPORTED_EXCHANGES:
            raise ValueError("Unsupported exchange.")

        if not self.symbol:
            raise ValueError("Symbol is required.")

        if self.market not in SUPPORTED_MARKETS:
            raise ValueError("Unsupported market.")

        if self.timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValueError("Unsupported timeframe.")

        if self.timestamp is None:
            raise ValueError("Timestamp is required.")

        if self.source_records <= 0:
            raise ValueError(
                "Source records must be greater than zero."
            )

        if not (0 <= self.data_quality_score <= 1):
            raise ValueError(
                "Quality score must be between 0 and 1."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def bullish_funding(self) -> bool:
        return (
            self.funding_rate is not None
            and self.funding_rate > 0
        )

    @property
    def bearish_funding(self) -> bool:
        return (
            self.funding_rate is not None
            and self.funding_rate < 0
        )

    @property
    def high_open_interest(self) -> bool:
        return (
            self.open_interest is not None
            and self.open_interest > 0
        )

    @property
    def high_iv(self) -> bool:
        return (
            self.implied_volatility is not None
            and self.implied_volatility > 0.80
        )

    @property
    def bullish_positioning(self) -> bool:
        return (
            self.long_short_ratio is not None
            and self.long_short_ratio > 1.0
        )

    @property
    def bearish_positioning(self) -> bool:
        return (
            self.long_short_ratio is not None
            and self.long_short_ratio < 1.0
        )

    @property
    def call_dominance(self) -> bool:
        return (
            self.put_call_ratio is not None
            and self.put_call_ratio < 1
        )

    @property
    def put_dominance(self) -> bool:
        return (
            self.put_call_ratio is not None
            and self.put_call_ratio > 1
        )