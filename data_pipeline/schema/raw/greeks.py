"""
Raw Greeks Schema

Defines the canonical schema for option Greeks collected from
cryptocurrency options exchanges.

Option Greeks measure the sensitivity of an option's price to changes
in the underlying asset price, volatility, time, and interest rates.

All exchange-specific Greeks data must be normalized into this schema
before validation and processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_MARKETS = {
    "options",
}

SUPPORTED_OPTION_TYPES = {
    "CALL",
    "PUT",
}


@dataclass
class GreeksSchema:
    """
    Canonical raw Greeks schema.
    """

    # ==========================================================
    # Source Information
    # ==========================================================

    exchange: str

    underlying_symbol: str

    option_symbol: str

    market: str

    source: Optional[str] = None

    # ==========================================================
    # Time Information
    # ==========================================================

    timestamp: datetime

    receive_time: Optional[datetime] = None

    expiration_date: Optional[datetime] = None

    # ==========================================================
    # Contract Information
    # ==========================================================

    strike_price: float

    option_type: str

    mark_price: Optional[float] = None

    underlying_price: Optional[float] = None

    implied_volatility: Optional[float] = None

    # ==========================================================
    # Greeks
    # ==========================================================

    delta: float

    gamma: float

    theta: float

    vega: float

    rho: float

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

        if not self.underlying_symbol:
            raise ValueError(
                "Underlying symbol is required."
            )

        if not self.option_symbol:
            raise ValueError(
                "Option symbol is required."
            )

        if self.market not in SUPPORTED_MARKETS:
            raise ValueError(
                f"Unsupported market: {self.market}"
            )

        if self.timestamp is None:
            raise ValueError(
                "Timestamp is required."
            )

        if self.strike_price <= 0:
            raise ValueError(
                "Strike price must be greater than zero."
            )

        if self.option_type not in SUPPORTED_OPTION_TYPES:
            raise ValueError(
                f"Unsupported option type: {self.option_type}"
            )

        if (
            self.mark_price is not None
            and self.mark_price < 0
        ):
            raise ValueError(
                "Mark price cannot be negative."
            )

        if (
            self.underlying_price is not None
            and self.underlying_price <= 0
        ):
            raise ValueError(
                "Underlying price must be greater than zero."
            )

        if (
            self.implied_volatility is not None
            and self.implied_volatility < 0
        ):
            raise ValueError(
                "Implied volatility cannot be negative."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def is_call(self) -> bool:
        return self.option_type == "CALL"

    @property
    def is_put(self) -> bool:
        return self.option_type == "PUT"

    @property
    def has_iv(self) -> bool:
        return self.implied_volatility is not None

    @property
    def has_mark_price(self) -> bool:
        return self.mark_price is not None