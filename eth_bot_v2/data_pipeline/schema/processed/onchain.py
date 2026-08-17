"""
Processed On-Chain Data Schema

Defines the canonical processed on-chain data schema used by the
ETH Bot AI Trading System.

This schema is generated after processing raw blockchain metrics from
multiple providers. Data is cleaned, validated, normalized, aggregated,
and synchronized before being used for feature engineering and AI models.

Sources may include:

- Glassnode
- CryptoQuant
- Dune Analytics
- Santiment
- IntoTheBlock
- Exchange Reserve APIs
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_NETWORKS = {
    "ethereum",
    "bitcoin",
    "bnb",
    "arbitrum",
    "optimism",
    "base",
    "polygon",
    "solana",
}

SUPPORTED_TIMEFRAMES = {
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
}


@dataclass
class ProcessedOnChainSchema:
    """
    Canonical processed on-chain schema.
    """

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str

    network: str

    timeframe: str

    timestamp: datetime

    # ==========================================================
    # Network Activity
    # ==========================================================

    transaction_count: Optional[int] = None

    active_addresses: Optional[int] = None

    new_addresses: Optional[int] = None

    block_count: Optional[int] = None

    gas_used: Optional[float] = None

    average_gas_price: Optional[float] = None

    transaction_fees: Optional[float] = None

    # ==========================================================
    # Token Metrics
    # ==========================================================

    transfer_volume: Optional[float] = None

    token_supply: Optional[float] = None

    exchange_balance: Optional[float] = None

    exchange_inflow: Optional[float] = None

    exchange_outflow: Optional[float] = None

    # ==========================================================
    # DeFi Metrics
    # ==========================================================

    total_value_locked: Optional[float] = None

    staking_balance: Optional[float] = None

    staking_ratio: Optional[float] = None

    # ==========================================================
    # Whale Activity
    # ==========================================================

    whale_transactions: Optional[int] = None

    whale_volume: Optional[float] = None

    large_transfer_count: Optional[int] = None

    # ==========================================================
    # Processing Metadata
    # ==========================================================

    processed_at: datetime

    source_records: int

    data_quality_score: float

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if not self.symbol:
            raise ValueError("Symbol is required.")

        if self.network not in SUPPORTED_NETWORKS:
            raise ValueError("Unsupported network.")

        if self.timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValueError("Unsupported timeframe.")

        if self.timestamp is None:
            raise ValueError("Timestamp is required.")

        if self.source_records <= 0:
            raise ValueError(
                "Source records must be greater than zero."
            )

        if not (0 <= self.data_quality_score <= 1):
            raise ValueError(
                "Data quality score must be between 0 and 1."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def exchange_netflow(self) -> Optional[float]:
        if (
            self.exchange_inflow is None
            or self.exchange_outflow is None
        ):
            return None

        return (
            self.exchange_inflow -
            self.exchange_outflow
        )

    @property
    def exchange_accumulation(self) -> bool:
        if self.exchange_netflow is None:
            return False

        return self.exchange_netflow < 0

    @property
    def exchange_distribution(self) -> bool:
        if self.exchange_netflow is None:
            return False

        return self.exchange_netflow > 0

    @property
    def high_whale_activity(self) -> bool:
        return (
            self.whale_transactions is not None
            and self.whale_transactions > 100
        )

    @property
    def network_growth(self) -> bool:
        return (
            self.new_addresses is not None
            and self.active_addresses is not None
            and self.new_addresses >
            self.active_addresses * 0.10
        )

    @property
    def staking_growth(self) -> bool:
        return (
            self.staking_ratio is not None
            and self.staking_ratio > 0.5
        )

    @property
    def healthy_network(self) -> bool:
        return (
            self.transaction_count is not None
            and self.active_addresses is not None
            and self.transaction_count > 0
            and self.active_addresses > 0
        )