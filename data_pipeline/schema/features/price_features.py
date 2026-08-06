"""
Price Features Schema

Defines engineered price-based features generated from
processed market data and technical indicators.

These features are designed for machine learning models,
strategy generation, and market regime detection.

This schema stores engineered features only.
Feature calculations are performed by the Feature Engineering Pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PriceFeatureSchema:

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str

    timeframe: str

    timestamp: datetime

    # ==========================================================
    # Returns
    # ==========================================================

    return_1: Optional[float] = None

    return_3: Optional[float] = None

    return_5: Optional[float] = None

    return_10: Optional[float] = None

    return_20: Optional[float] = None

    return_50: Optional[float] = None

    return_100: Optional[float] = None

    return_200: Optional[float] = None

    log_return_1: Optional[float] = None

    log_return_5: Optional[float] = None

    log_return_20: Optional[float] = None

    # ==========================================================
    # Price Change
    # ==========================================================

    close_change: Optional[float] = None

    high_change: Optional[float] = None

    low_change: Optional[float] = None

    open_change: Optional[float] = None

    percent_change: Optional[float] = None

    # ==========================================================
    # Candle Features
    # ==========================================================

    body_size: Optional[float] = None

    upper_shadow: Optional[float] = None

    lower_shadow: Optional[float] = None

    total_range: Optional[float] = None

    body_ratio: Optional[float] = None

    upper_shadow_ratio: Optional[float] = None

    lower_shadow_ratio: Optional[float] = None

    # ==========================================================
    # Price Position
    # ==========================================================

    close_position: Optional[float] = None

    high_low_ratio: Optional[float] = None

    open_close_ratio: Optional[float] = None

    # ==========================================================
    # Gap Features
    # ==========================================================

    gap_size: Optional[float] = None

    gap_percent: Optional[float] = None

    # ==========================================================
    # Rolling Statistics
    # ==========================================================

    rolling_mean_20: Optional[float] = None

    rolling_std_20: Optional[float] = None

    rolling_min_20: Optional[float] = None

    rolling_max_20: Optional[float] = None

    rolling_median_20: Optional[float] = None

    # ==========================================================
    # Distance Features
    # ==========================================================

    distance_from_high: Optional[float] = None

    distance_from_low: Optional[float] = None

    distance_from_sma20: Optional[float] = None

    distance_from_sma50: Optional[float] = None

    distance_from_ema20: Optional[float] = None

    distance_from_ema50: Optional[float] = None

    # ==========================================================
    # Price Velocity
    # ==========================================================

    velocity: Optional[float] = None

    acceleration: Optional[float] = None

    # ==========================================================
    # Metadata
    # ==========================================================

    feature_version: str = "1.0"

    calculated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def bullish_candle(self) -> bool:
        return (
            self.close_change is not None
            and self.close_change > 0
        )

    @property
    def bearish_candle(self) -> bool:
        return (
            self.close_change is not None
            and self.close_change < 0
        )

    @property
    def strong_body(self) -> bool:
        return (
            self.body_ratio is not None
            and self.body_ratio >= 0.70
        )

    @property
    def doji_like(self) -> bool:
        return (
            self.body_ratio is not None
            and self.body_ratio <= 0.10
        )

    @property
    def bullish_gap(self) -> bool:
        return (
            self.gap_percent is not None
            and self.gap_percent > 0
        )

    @property
    def bearish_gap(self) -> bool:
        return (
            self.gap_percent is not None
            and self.gap_percent < 0
        )