"""
Raw Order Book Schema

Defines the canonical schema for raw order book (market depth) data
collected from cryptocurrency exchanges.

Every exchange-specific order book snapshot or update must be normalized
into this schema before validation and processing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


SUPPORTED_MARKETS = {
    "spot",
    "futures",
    "coinm",
}


@dataclass
class OrderBookLevel:
    """
    Represents a single price level in the order book.
    """

    price: float

    quantity: float

    order_count: Optional[int] = None

    def validate(self):

        if self.price <= 0:
            raise ValueError("Price must be greater than zero.")

        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        if self.order_count is not None and self.order_count < 0:
            raise ValueError("Order count cannot be negative.")

        return True


@dataclass
class OrderBookSchema:
    """
    Canonical raw order book schema.
    """

    # ------------------------------------------------------------------
    # Source Information
    # ------------------------------------------------------------------

    exchange: str

    symbol: str

    market: str

    # ------------------------------------------------------------------
    # Snapshot Information
    # ------------------------------------------------------------------

    timestamp: datetime

    receive_time: datetime

    sequence_id: Optional[int] = None

    update_id: Optional[int] = None

    checksum: Optional[str] = None

    # ------------------------------------------------------------------
    # Market Depth
    # ------------------------------------------------------------------

    bids: List[OrderBookLevel] = field(default_factory=list)

    asks: List[OrderBookLevel] = field(default_factory=list)

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

        if self.receive_time is None:
            raise ValueError("Receive time is required.")

        if len(self.bids) == 0:
            raise ValueError("Order book must contain bids.")

        if len(self.asks) == 0:
            raise ValueError("Order book must contain asks.")

        # Validate every level
        for level in self.bids:
            level.validate()

        for level in self.asks:
            level.validate()

        # Highest bid
        best_bid = max(level.price for level in self.bids)

        # Lowest ask
        best_ask = min(level.price for level in self.asks)

        if best_bid >= best_ask:
            raise ValueError(
                "Best bid cannot be greater than or equal to best ask."
            )

        return True

    # ------------------------------------------------------------------
    # Convenience Properties
    # ------------------------------------------------------------------

    @property
    def best_bid(self):

        return max(level.price for level in self.bids)

    @property
    def best_ask(self):

        return min(level.price for level in self.asks)

    @property
    def spread(self):

        return self.best_ask - self.best_bid

    @property
    def mid_price(self):

        return (self.best_bid + self.best_ask) / 2