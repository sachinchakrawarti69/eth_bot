"""
Raw Open Interest Schema

Defines the canonical schema for raw Open Interest (OI) data collected
from cryptocurrency derivative exchanges.

Open Interest (OI) represents the total number of outstanding derivative
contracts that remain open. It is one of the most important metrics for
analyzing futures market participation and leverage.

Every exchange-specific response must be normalized into this schema
before validation and processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_MARKETS = {
    "futures",
    "coinm",
    "options",
}

SUPPORTED_CONTRACT_TYPES = {
    "PERPETUAL",
    "CURRENT_QUARTER",
    "NEXT_QUARTER",
    "MONTHLY",
    "OPTIONS",
}


@dataclass
class OpenInterestSchema:
    """
    Canonical raw Open Interest schema.
    """

    # ==========================================================
    # Source Information
    # ==========================================================

    exchange: str

    symbol: str

    market: str

    source: Optional[str] = None

    # ==========================================================
    # Time Information
    # ==========================================================

    timestamp: datetime

    receive_time: Optional[datetime] = None

    timeframe: Optional[str] = None

    # ==========================================================
    # Open Interest Information
    # ==========================================================

    open_interest: float

    open_interest_value: Optional[float] = None

    currency: Optional[str] = None

    contract_type: Optional[str] = None

    # ==========================================================
    # Exchange Metadata
    # ==========================================================

    update_id: Optional[int] = None

    sequence_id: Optional[int] = None

    # ==========================================================
    # Validation
    # ==========================================================

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
            raise ValueError(
                "Timestamp is required."
            )

        if self.open_interest < 0:
            raise ValueError(
                "Open Interest cannot be negative."
            )

        if (
            self.open_interest_value is not None
            and self.open_interest_value < 0
        ):
            raise ValueError(
                "Open Interest value cannot be negative."
            )

        if (
            self.contract_type is not None
            and self.contract_type
            not in SUPPORTED_CONTRACT_TYPES
        ):
            raise ValueError(
                f"Unsupported contract type: {self.contract_type}"
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def has_notional_value(self) -> bool:
        return self.open_interest_value is not None

    @property
    def is_snapshot(self) -> bool:
        return self.timeframe is None

    @property
    def is_perpetual(self) -> bool:
        return self.contract_type == "PERPETUAL"

    @property
    def is_options(self) -> bool:
        return self.market == "options"

    @property
    def is_futures(self) -> bool:
        return self.market in {
            "futures",
            "coinm",
        }