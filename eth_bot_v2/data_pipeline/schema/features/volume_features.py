"""
Volume Features Schema

Defines engineered volume-based features generated from
processed market data and volume indicators.

These features capture trading activity, liquidity,
buying/selling pressure, and abnormal volume behaviour.

This schema stores engineered features only.
Feature calculations are performed by the Feature Engineering Pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VolumeFeatureSchema:

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str

    timeframe: str

    timestamp: datetime

    # ==========================================================
    # Raw Volume Features
    # ==========================================================

    volume: Optional[float] = None

    quote_volume: Optional[float] = None

    trade_count: Optional[int] = None

    buy_volume: Optional[float] = None

    sell_volume: Optional[float] = None

    # ==========================================================
    # Relative Volume
    # ==========================================================

    relative_volume_5: Optional[float] = None

    relative_volume_20: Optional[float] = None

    relative_volume_50: Optional[float] = None

    # ==========================================================
    # Volume Statistics
    # ==========================================================

    rolling_volume_mean_20: Optional[float] = None

    rolling_volume_std_20: Optional[float] = None

    rolling_volume_min_20: Optional[float] = None

    rolling_volume_max_20: Optional[float] = None

    rolling_volume_median_20: Optional[float] = None

    # ==========================================================
    # Volume Change
    # ==========================================================

    volume_change: Optional[float] = None

    volume_percent_change: Optional[float] = None

    volume_growth_rate: Optional[float] = None

    # ==========================================================
    # Buying / Selling Pressure
    # ==========================================================

    buy_sell_ratio: Optional[float] = None

    buy_pressure: Optional[float] = None

    sell_pressure: Optional[float] = None

    volume_imbalance: Optional[float] = None

    # ==========================================================
    # Liquidity Features
    # ==========================================================

    liquidity_score: Optional[float] = None

    average_trade_size: Optional[float] = None

    turnover_rate: Optional[float] = None

    # ==========================================================
    # VWAP Features
    # ==========================================================

    distance_from_vwap: Optional[float] = None

    price_above_vwap: Optional[bool] = None

    # ==========================================================
    # Volume Profile Features
    # ==========================================================

    volume_node_strength: Optional[float] = None

    high_volume_node_distance: Optional[float] = None

    low_volume_node_distance: Optional[float] = None

    # ==========================================================
    # Metadata
    # ==========================================================

    feature_version: str = "1.0"

    calculated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def high_relative_volume(self) -> bool:
        return (
            self.relative_volume_20 is not None
            and self.relative_volume_20 >= 1.5
        )

    @property
    def low_relative_volume(self) -> bool:
        return (
            self.relative_volume_20 is not None
            and self.relative_volume_20 <= 0.7
        )

    @property
    def bullish_volume(self) -> bool:
        return (
            self.buy_pressure is not None
            and self.sell_pressure is not None
            and self.buy_pressure > self.sell_pressure
        )

    @property
    def bearish_volume(self) -> bool:
        return (
            self.buy_pressure is not None
            and self.sell_pressure is not None
            and self.sell_pressure > self.buy_pressure
        )

    @property
    def strong_liquidity(self) -> bool:
        return (
            self.liquidity_score is not None
            and self.liquidity_score >= 0.80
        )

    @property
    def weak_liquidity(self) -> bool:
        return (
            self.liquidity_score is not None
            and self.liquidity_score <= 0.30
        )