"""
Raw Liquidation Schema

Defines the canonical schema for raw liquidation events collected from
cryptocurrency derivative exchanges.

A liquidation occurs when a trader's leveraged position is forcibly closed
by the exchange because the account can no longer satisfy the required
maintenance margin.

All exchange-specific liquidation events must be normalized into this
schema before validation and processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_MARKETS = {
    "futures",
    "coinm",
    "options",
}

SUPPORTED_SIDES = {
    "LONG",
    "SHORT",
}


@dataclass
class LiquidationSchema:
    """
    Canonical raw liquidation schema.
    """

    # ------------------------------------------------------------------
    # Source Information
    # ------------------------------------------------------------------

    exchange: str

    symbol: str

    market: str

    # ------------------------------------------------------------------
    # Event Information
    # ------------------------------------------------------------------

    event_id: str

    timestamp: datetime

    receive_time: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Liquidation Details
    # ------------------------------------------------------------------

    side: str

    price: float

    quantity: float

    notional_value: float

    currency: Optional[str] = None

    leverage: Optional[float] = None

    contract_type: Optional[str] = None

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    source: Optional[str] = None

    sequence_id: Optional[int] = None

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

        if not self.event_id:
            raise ValueError("Event ID is required.")

        if self.timestamp is None:
            raise ValueError("Timestamp is required.")

        if self.side not in SUPPORTED_SIDES:
            raise ValueError(
                f"Unsupported side: {self.side}"
            )

        if self.price <= 0:
            raise ValueError(
                "Price must be greater than zero."
            )

        if self.quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        if self.notional_value <= 0:
            raise ValueError(
                "Notional value must be greater than zero."
            )

        if (
            self.leverage is not None
            and self.leverage <= 0
        ):
            raise ValueError(
                "Leverage must be greater than zero."
            )

        return True

    # ------------------------------------------------------------------
    # Convenience Properties
    # ------------------------------------------------------------------

    @property
    def is_long_liquidation(self) -> bool:
        return self.side == "LONG"

    @property
    def is_short_liquidation(self) -> bool:
        return self.side == "SHORT"