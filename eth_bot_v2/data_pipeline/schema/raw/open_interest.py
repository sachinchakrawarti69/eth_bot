"""
Raw Open Interest Schema

Defines the canonical schema for raw Open Interest (OI) data collected
from cryptocurrency exchanges.

Open Interest represents the total number of outstanding derivative
contracts (futures/perpetuals/options) that are currently open.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_MARKETS = {
    "futures",
    "coinm",
    "options",
}


@dataclass
class OpenInterestSchema:
    """
    Canonical raw Open Interest schema.
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
    # Open Interest Data
    # ------------------------------------------------------------------

    open_interest: float

    open_interest_value: Optional[float] = None

    currency: Optional[str] = None

    contract_type: Optional[str] = None

    # ------------------------------------------------------------------
    # Optional Metadata
    # ------------------------------------------------------------------

    update_id: Optional[int] = None

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

        if self.open_interest < 0:
            raise ValueError(
                "Open interest cannot be negative."
            )

        if (
            self.open_interest_value is not None
            and self.open_interest_value < 0
        ):
            raise ValueError(
                "Open interest value cannot be negative."
            )

        return True

    # ------------------------------------------------------------------
    # Convenience Properties
    # ------------------------------------------------------------------

    @property
    def has_notional_value(self) -> bool:
        return self.open_interest_value is not None

    @property
    def is_snapshot(self) -> bool:
        return self.timeframe is None