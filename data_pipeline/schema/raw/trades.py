"""
Raw Trades Schema

Defines the canonical schema for raw trade (tick-by-tick) data collected
from cryptocurrency exchanges.

All exchanges must be normalized into this schema before entering the
validation and processing pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_MARKETS = {
    "spot",
    "futures",
    "coinm",
}


SUPPORTED_SIDES = {
    "BUY",
    "SELL",
}


@dataclass
class TradeSchema:
    """
    Canonical raw trade schema.
    """

    # ------------------------------------------------------------------
    # Source Information
    # ------------------------------------------------------------------

    exchange: str

    symbol: str

    market: str

    # ------------------------------------------------------------------
    # Trade Information
    # ------------------------------------------------------------------

    trade_id: str

    price: float

    quantity: float

    quote_quantity: float

    side: str

    trade_time: datetime

    # ------------------------------------------------------------------
    # Optional Fields
    # ------------------------------------------------------------------

    buyer_order_id: Optional[str] = None

    seller_order_id: Optional[str] = None

    is_market_maker: Optional[bool] = None

    sequence: Optional[int] = None

    receive_time: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self):

        if not self.exchange:
            raise ValueError("Exchange is required.")

        if not self.symbol:
            raise ValueError("Symbol is required.")

        if self.market not in SUPPORTED_MARKETS:
            raise ValueError(f"Unsupported market: {self.market}")

        if not self.trade_id:
            raise ValueError("Trade ID is required.")

        if self.price <= 0:
            raise ValueError("Price must be greater than zero.")

        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        if self.quote_quantity < 0:
            raise ValueError("Quote quantity cannot be negative.")

        if self.side not in SUPPORTED_SIDES:
            raise ValueError(
                f"Unsupported trade side: {self.side}"
            )

        if self.trade_time is None:
            raise ValueError("Trade time is required.")

        return True