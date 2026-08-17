"""
Raw Implied Volatility Schema

Defines the canonical schema for raw Implied Volatility (IV) data
collected from cryptocurrency options exchanges.

Implied Volatility represents the market's expectation of future
volatility inferred from option prices.

All exchange-specific IV data must be normalized into this schema
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
class ImpliedVolatilitySchema:
    """
    Canonical raw Implied Volatility schema.
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

    timeframe: Optional[str] = None

    # ==========================================================
    # Contract Information
    # ==========================================================

    strike_price: float

    option_type: str

    underlying_price: float

    mark_price: Optional[float] = None

    # ==========================================================
    # Volatility Information
    # ==========================================================

    implied_volatility: float

    bid_iv: Optional[float] = None

    ask_iv: Optional[float] = None

    mark_iv: Optional[float] = None

    historical_volatility: Optional[float] = None

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

        if self.underlying_price <= 0:
            raise ValueError(
                "Underlying price must be greater than zero."
            )

        if self.implied_volatility < 0:
            raise ValueError(
                "Implied volatility cannot be negative."
            )

        for value in (
            self.bid_iv,
            self.ask_iv,
            self.mark_iv,
            self.historical_volatility,
        ):
            if value is not None and value < 0:
                raise ValueError(
                    "Volatility values cannot be negative."
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
    def has_bid_ask_iv(self) -> bool:
        return (
            self.bid_iv is not None
            and self.ask_iv is not None
        )

    @property
    def has_historical_volatility(self) -> bool:
        return self.historical_volatility is not None