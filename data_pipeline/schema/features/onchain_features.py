"""
On-Chain Features Schema

Defines engineered on-chain features generated from processed
blockchain data.

These features summarize blockchain activity, network health,
whale behavior, exchange flows, and capital movement into
AI-ready numerical features.

This schema stores engineered features only.
Feature calculations are performed by the Feature Engineering Pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OnChainFeatureSchema:

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str
    timeframe: str
    timestamp: datetime

    # ==========================================================
    # Network Activity
    # ==========================================================

    active_addresses: Optional[float] = None

    new_addresses: Optional[float] = None

    transaction_count: Optional[float] = None

    transaction_volume: Optional[float] = None

    gas_used: Optional[float] = None

    gas_price: Optional[float] = None

    # ==========================================================
    # Exchange Flow
    # ==========================================================

    exchange_inflow: Optional[float] = None

    exchange_outflow: Optional[float] = None

    net_exchange_flow: Optional[float] = None

    exchange_reserve: Optional[float] = None

    reserve_change: Optional[float] = None

    # ==========================================================
    # Whale Activity
    # ==========================================================

    whale_transaction_count: Optional[int] = None

    whale_volume: Optional[float] = None

    whale_accumulation_score: Optional[float] = None

    whale_distribution_score: Optional[float] = None

    # ==========================================================
    # Holder Metrics
    # ==========================================================

    long_term_holder_ratio: Optional[float] = None

    short_term_holder_ratio: Optional[float] = None

    holder_growth_rate: Optional[float] = None

    # ==========================================================
    # Network Health
    # ==========================================================

    network_activity_score: Optional[float] = None

    network_growth_score: Optional[float] = None

    network_congestion_score: Optional[float] = None

    # ==========================================================
    # Capital Flow
    # ==========================================================

    capital_inflow_score: Optional[float] = None

    capital_outflow_score: Optional[float] = None

    capital_flow_balance: Optional[float] = None

    # ==========================================================
    # Composite Features
    # ==========================================================

    onchain_sentiment_score: Optional[float] = None

    accumulation_score: Optional[float] = None

    distribution_score: Optional[float] = None

    smart_money_score: Optional[float] = None

    # ==========================================================
    # Metadata
    # ==========================================================

    feature_version: str = "1.0"

    calculated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def whale_accumulation(self) -> bool:
        return (
            self.whale_accumulation_score is not None
            and self.whale_accumulation_score >= 0.70
        )

    @property
    def whale_distribution(self) -> bool:
        return (
            self.whale_distribution_score is not None
            and self.whale_distribution_score >= 0.70
        )

    @property
    def bullish_exchange_flow(self) -> bool:
        return (
            self.net_exchange_flow is not None
            and self.net_exchange_flow < 0
        )

    @property
    def bearish_exchange_flow(self) -> bool:
        return (
            self.net_exchange_flow is not None
            and self.net_exchange_flow > 0
        )

    @property
    def healthy_network(self) -> bool:
        return (
            self.network_activity_score is not None
            and self.network_activity_score >= 0.80
        )

    @property
    def smart_money_buying(self) -> bool:
        return (
            self.smart_money_score is not None
            and self.smart_money_score >= 0.75
        )