"""
Order Book Features Schema

Defines engineered features derived from processed order book data.

These features describe market microstructure, liquidity,
buying/selling pressure, and order book imbalance for use in
machine learning models, strategy generation, and execution.

This schema stores engineered features only.
Feature calculations are performed by the Feature Engineering Pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OrderBookFeatureSchema:

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str
    timeframe: str
    timestamp: datetime

    # ==========================================================
    # Best Bid / Ask
    # ==========================================================

    best_bid_price: Optional[float] = None
    best_ask_price: Optional[float] = None

    best_bid_size: Optional[float] = None
    best_ask_size: Optional[float] = None

    spread: Optional[float] = None
    spread_percent: Optional[float] = None

    mid_price: Optional[float] = None

    # ==========================================================
    # Order Book Imbalance
    # ==========================================================

    bid_volume: Optional[float] = None
    ask_volume: Optional[float] = None

    orderbook_imbalance: Optional[float] = None

    bid_ask_ratio: Optional[float] = None

    # ==========================================================
    # Liquidity
    # ==========================================================

    liquidity_score: Optional[float] = None

    market_depth_5: Optional[float] = None
    market_depth_10: Optional[float] = None
    market_depth_20: Optional[float] = None

    # ==========================================================
    # Order Flow
    # ==========================================================

    order_flow_imbalance: Optional[float] = None

    aggressive_buy_volume: Optional[float] = None
    aggressive_sell_volume: Optional[float] = None

    cancellation_ratio: Optional[float] = None

    # ==========================================================
    # Slippage
    # ==========================================================

    estimated_buy_slippage: Optional[float] = None
    estimated_sell_slippage: Optional[float] = None

    execution_cost: Optional[float] = None

    # ==========================================================
    # Price Pressure
    # ==========================================================

    buying_pressure: Optional[float] = None
    selling_pressure: Optional[float] = None

    pressure_difference: Optional[float] = None

    # ==========================================================
    # Order Book Dynamics
    # ==========================================================

    orderbook_volatility: Optional[float] = None

    imbalance_change: Optional[float] = None

    liquidity_change: Optional[float] = None

    # ==========================================================
    # Metadata
    # ==========================================================

    feature_version: str = "1.0"

    calculated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def bullish_orderbook(self) -> bool:
        return (
            self.orderbook_imbalance is not None
            and self.orderbook_imbalance > 0.20
        )

    @property
    def bearish_orderbook(self) -> bool:
        return (
            self.orderbook_imbalance is not None
            and self.orderbook_imbalance < -0.20
        )

    @property
    def high_liquidity(self) -> bool:
        return (
            self.liquidity_score is not None
            and self.liquidity_score >= 0.80
        )

    @property
    def low_liquidity(self) -> bool:
        return (
            self.liquidity_score is not None
            and self.liquidity_score <= 0.30
        )

    @property
    def buy_pressure_dominant(self) -> bool:
        return (
            self.buying_pressure is not None
            and self.selling_pressure is not None
            and self.buying_pressure > self.selling_pressure
        )

    @property
    def sell_pressure_dominant(self) -> bool:
        return (
            self.buying_pressure is not None
            and self.selling_pressure is not None
            and self.selling_pressure > self.buying_pressure
        )