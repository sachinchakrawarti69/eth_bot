"""
Raw Fear & Greed Index Schema

Defines the canonical schema for Fear & Greed Index data collected from
market sentiment providers.

The Fear & Greed Index is a sentiment indicator that measures whether
market participants are driven by fear or greed. It is commonly used as
a contrarian indicator for market analysis.

All provider-specific responses must be normalized into this schema
before validation and processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_SENTIMENTS = {
    "EXTREME_FEAR",
    "FEAR",
    "NEUTRAL",
    "GREED",
    "EXTREME_GREED",
}


SUPPORTED_SOURCES = {
    "ALTERNATIVE_ME",
    "CNN",
    "CUSTOM",
}


@dataclass
class FearGreedSchema:
    """
    Canonical raw Fear & Greed Index schema.
    """

    # ==========================================================
    # Source Information
    # ==========================================================

    source: str

    provider: str

    # ==========================================================
    # Time Information
    # ==========================================================

    timestamp: datetime

    receive_time: Optional[datetime] = None

    # ==========================================================
    # Index Information
    # ==========================================================

    value: int

    sentiment: str

    previous_value: Optional[int] = None

    change: Optional[int] = None

    # ==========================================================
    # Optional Metadata
    # ==========================================================

    methodology_version: Optional[str] = None

    update_frequency: Optional[str] = None

    next_update: Optional[datetime] = None

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if not self.source:
            raise ValueError(
                "Source is required."
            )

        if self.source not in SUPPORTED_SOURCES:
            raise ValueError(
                f"Unsupported source: {self.source}"
            )

        if not self.provider:
            raise ValueError(
                "Provider is required."
            )

        if self.timestamp is None:
            raise ValueError(
                "Timestamp is required."
            )

        if not (0 <= self.value <= 100):
            raise ValueError(
                "Fear & Greed value must be between 0 and 100."
            )

        if self.sentiment not in SUPPORTED_SENTIMENTS:
            raise ValueError(
                f"Unsupported sentiment: {self.sentiment}"
            )

        if (
            self.previous_value is not None
            and not (0 <= self.previous_value <= 100)
        ):
            raise ValueError(
                "Previous value must be between 0 and 100."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def is_extreme_fear(self) -> bool:
        return self.sentiment == "EXTREME_FEAR"

    @property
    def is_fear(self) -> bool:
        return self.sentiment == "FEAR"

    @property
    def is_neutral(self) -> bool:
        return self.sentiment == "NEUTRAL"

    @property
    def is_greed(self) -> bool:
        return self.sentiment == "GREED"

    @property
    def is_extreme_greed(self) -> bool:
        return self.sentiment == "EXTREME_GREED"

    @property
    def bullish(self) -> bool:
        return self.value >= 50

    @property
    def bearish(self) -> bool:
        return self.value < 50

    @property
    def normalized_score(self) -> float:
        """
        Returns score normalized to 0.0 - 1.0.
        """
        return self.value / 100.0