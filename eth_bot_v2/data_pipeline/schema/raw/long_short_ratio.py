"""
Raw Long/Short Ratio Schema

Defines the canonical schema for Long/Short Ratio data collected from
cryptocurrency derivative exchanges.

The Long/Short Ratio measures the balance between long and short positions
held by traders. It is commonly provided by exchanges for top traders,
accounts, or positions.

All exchange-specific responses must be normalized into this schema before
validation and processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_MARKETS = {
    "futures",
    "coinm",
}

SUPPORTED_RATIO_TYPES = {
    "ACCOUNT",
    "POSITION",
    "TOP_TRADER_ACCOUNT",
    "TOP_TRADER_POSITION",
    "GLOBAL",
}


@dataclass
class LongShortRatioSchema:
    """
    Canonical raw Long/Short Ratio schema.
    """

    # ------------------------------------------------------------------
    # Source Information
    # ------------------------------------------------------------------

    exchange: str

    symbol: str

    market: str

    # ------------------------------------------------------------------
    # Time Information
    # ------------------------------------------------------------------

    timestamp: datetime

    receive_time: Optional[datetime] = None

    timeframe: Optional[str] = None

    # ------------------------------------------------------------------
    # Ratio Information
    # ------------------------------------------------------------------

    ratio_type: str

    long_ratio: float

    short_ratio: float

    long_short_ratio: float

    # ------------------------------------------------------------------
    # Optional Metadata
    # ------------------------------------------------------------------

    long_accounts: Optional[int] = None

    short_accounts: Optional[int] = None

    source: Optional[str] = None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self):

        if not self.exchange:
            raise ValueError("Exchange is required.")

        if not self.symbol:
            raise ValueError("Symbol is required.")

        if self.market not in SUPPORTED_MARKETS:
            raise ValueError(
                f"Unsupported market: {self.market}"
            )

        if self.timestamp is None:
            raise ValueError("Timestamp is required.")

        if self.ratio_type not in SUPPORTED_RATIO_TYPES:
            raise ValueError(
                f"Unsupported ratio type: {self.ratio_type}"
            )

        if self.long_ratio < 0:
            raise ValueError("Long ratio cannot be negative.")

        if self.short_ratio < 0:
            raise ValueError("Short ratio cannot be negative.")

        if self.long_short_ratio < 0:
            raise ValueError(
                "Long/Short ratio cannot be negative."
            )

        if (
            self.long_accounts is not None
            and self.long_accounts < 0
        ):
            raise ValueError(
                "Long account count cannot be negative."
            )

        if (
            self.short_accounts is not None
            and self.short_accounts < 0
        ):
            raise ValueError(
                "Short account count cannot be negative."
            )

        return True

    # ------------------------------------------------------------------
    # Convenience Properties
    # ------------------------------------------------------------------

    @property
    def bullish(self) -> bool:
        return self.long_short_ratio > 1.0

    @property
    def bearish(self) -> bool:
        return self.long_short_ratio < 1.0

    @property
    def neutral(self) -> bool:
        return self.long_short_ratio == 1.0