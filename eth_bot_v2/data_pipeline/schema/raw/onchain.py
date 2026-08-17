"""
Raw On-Chain Data Schema

Defines the canonical schema for blockchain on-chain metrics collected
from blockchain nodes, analytics providers, and data platforms.

On-chain data represents blockchain activity including transactions,
wallet activity, network usage, token movements, and protocol metrics.

All provider-specific blockchain responses must be normalized into this
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


SUPPORTED_METRIC_TYPES = {
    "TRANSACTION_COUNT",
    "ACTIVE_ADDRESSES",
    "NEW_ADDRESSES",
    "GAS_USAGE",
    "GAS_PRICE",
    "BLOCK_COUNT",
    "TRANSFER_VOLUME",
    "TOKEN_SUPPLY",
    "EXCHANGE_BALANCE",
    "WALLET_BALANCE",
    "TVL",
    "STAKING",
    "FEES",
}


SUPPORTED_TIMEFRAMES = {
    "1m",
    "5m",
    "15m",
    "1h",
    "4h",
    "1d",
    "1w",
}


@dataclass
class OnChainSchema:
    """
    Canonical raw on-chain data schema.
    """

    # ==========================================================
    # Source Information
    # ==========================================================

    source: str

    provider: str

    network: str

    # ==========================================================
    # Metric Information
    # ==========================================================

    metric_type: str

    metric_name: str

    value: float

    unit: str

    # ==========================================================
    # Time Information
    # ==========================================================

    timestamp: datetime

    receive_time: Optional[datetime] = None

    timeframe: Optional[str] = None

    # ==========================================================
    # Asset Information
    # ==========================================================

    asset_symbol: Optional[str] = None

    contract_address: Optional[str] = None

    # ==========================================================
    # Blockchain Metadata
    # ==========================================================

    block_number: Optional[int] = None

    transaction_hash: Optional[str] = None

    wallet_address: Optional[str] = None

    # ==========================================================
    # Additional Metadata
    # ==========================================================

    metadata: Optional[dict] = None

    source_url: Optional[str] = None

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if not self.source:
            raise ValueError(
                "Source is required."
            )

        if not self.provider:
            raise ValueError(
                "Provider is required."
            )

        if self.network not in SUPPORTED_NETWORKS:
            raise ValueError(
                f"Unsupported network: {self.network}"
            )

        if self.metric_type not in SUPPORTED_METRIC_TYPES:
            raise ValueError(
                f"Unsupported metric type: {self.metric_type}"
            )

        if not self.metric_name:
            raise ValueError(
                "Metric name is required."
            )

        if self.timestamp is None:
            raise ValueError(
                "Timestamp is required."
            )

        if self.value < 0:
            raise ValueError(
                "Metric value cannot be negative."
            )

        if (
            self.timeframe is not None
            and self.timeframe not in SUPPORTED_TIMEFRAMES
        ):
            raise ValueError(
                f"Unsupported timeframe: {self.timeframe}"
            )

        if (
            self.block_number is not None
            and self.block_number < 0
        ):
            raise ValueError(
                "Block number cannot be negative."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def is_wallet_metric(self) -> bool:
        return self.metric_type in {
            "ACTIVE_ADDRESSES",
            "NEW_ADDRESSES",
            "WALLET_BALANCE",
        }

    @property
    def is_market_metric(self) -> bool:
        return self.metric_type in {
            "TRANSFER_VOLUME",
            "EXCHANGE_BALANCE",
            "TOKEN_SUPPLY",
        }

    @property
    def is_network_metric(self) -> bool:
        return self.metric_type in {
            "TRANSACTION_COUNT",
            "GAS_USAGE",
            "GAS_PRICE",
            "BLOCK_COUNT",
            "FEES",
        }

    @property
    def has_block_reference(self) -> bool:
        return self.block_number is not None

    @property
    def has_wallet_reference(self) -> bool:
        return self.wallet_address is not None