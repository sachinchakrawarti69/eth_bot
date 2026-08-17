"""
Raw Whale Activity Schema

Defines the canonical schema for whale activity collected from
blockchain analytics providers and exchange monitoring services.

A whale is typically an individual wallet, institution, exchange,
or smart contract that moves a significant amount of cryptocurrency.

All provider-specific whale events should be normalized into this
schema before validation and processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_NETWORKS = {
    "ETHEREUM",
    "BITCOIN",
    "BNB",
    "ARBITRUM",
    "OPTIMISM",
    "BASE",
    "POLYGON",
    "SOLANA",
}

SUPPORTED_EVENT_TYPES = {
    "TRANSFER",
    "EXCHANGE_INFLOW",
    "EXCHANGE_OUTFLOW",
    "WHALE_ALERT",
    "TOKEN_MINT",
    "TOKEN_BURN",
}

SUPPORTED_DIRECTIONS = {
    "IN",
    "OUT",
    "INTERNAL",
}


@dataclass
class WhaleActivitySchema:
    """
    Canonical raw whale activity schema.
    """

    # ==========================================================
    # Source Information
    # ==========================================================

    source: str

    provider: str

    network: str

    # ==========================================================
    # Event Information
    # ==========================================================

    event_id: str

    timestamp: datetime

    receive_time: Optional[datetime] = None

    event_type: str

    # ==========================================================
    # Asset Information
    # ==========================================================

    asset_symbol: str

    amount: float

    usd_value: float

    transaction_hash: str

    # ==========================================================
    # Wallet Information
    # ==========================================================

    from_address: str

    to_address: str

    from_label: Optional[str] = None

    to_label: Optional[str] = None

    direction: str = "INTERNAL"

    # ==========================================================
    # Metadata
    # ==========================================================

    block_number: Optional[int] = None

    transaction_fee: Optional[float] = None

    confirmations: Optional[int] = None

    source_url: Optional[str] = None

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if not self.source:
            raise ValueError("Source is required.")

        if not self.provider:
            raise ValueError("Provider is required.")

        if self.network not in SUPPORTED_NETWORKS:
            raise ValueError(
                f"Unsupported network: {self.network}"
            )

        if not self.event_id:
            raise ValueError("Event ID is required.")

        if self.timestamp is None:
            raise ValueError("Timestamp is required.")

        if self.event_type not in SUPPORTED_EVENT_TYPES:
            raise ValueError(
                f"Unsupported event type: {self.event_type}"
            )

        if not self.asset_symbol:
            raise ValueError(
                "Asset symbol is required."
            )

        if self.amount <= 0:
            raise ValueError(
                "Amount must be greater than zero."
            )

        if self.usd_value <= 0:
            raise ValueError(
                "USD value must be greater than zero."
            )

        if not self.transaction_hash:
            raise ValueError(
                "Transaction hash is required."
            )

        if not self.from_address:
            raise ValueError(
                "From address is required."
            )

        if not self.to_address:
            raise ValueError(
                "To address is required."
            )

        if self.direction not in SUPPORTED_DIRECTIONS:
            raise ValueError(
                f"Unsupported direction: {self.direction}"
            )

        if (
            self.block_number is not None
            and self.block_number < 0
        ):
            raise ValueError(
                "Block number cannot be negative."
            )

        if (
            self.transaction_fee is not None
            and self.transaction_fee < 0
        ):
            raise ValueError(
                "Transaction fee cannot be negative."
            )

        if (
            self.confirmations is not None
            and self.confirmations < 0
        ):
            raise ValueError(
                "Confirmations cannot be negative."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def is_exchange_inflow(self) -> bool:
        return self.event_type == "EXCHANGE_INFLOW"

    @property
    def is_exchange_outflow(self) -> bool:
        return self.event_type == "EXCHANGE_OUTFLOW"

    @property
    def is_transfer(self) -> bool:
        return self.event_type == "TRANSFER"

    @property
    def is_large_transaction(self) -> bool:
        """
        Returns True if transaction value exceeds $1M.
        """
        return self.usd_value >= 1_000_000

    @property
    def is_confirmed(self) -> bool:
        return (
            self.confirmations is not None
            and self.confirmations > 0
        )