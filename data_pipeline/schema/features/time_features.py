"""
Time Features Schema

Defines engineered temporal features generated from timestamps.

These features capture cyclical market behavior, trading sessions,
calendar effects, and periodic patterns that influence market
activity and improve machine learning models.

This schema stores engineered features only.
Feature calculations are performed by the Feature Engineering Pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TimeFeatureSchema:

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str
    timeframe: str
    timestamp: datetime

    # ==========================================================
    # Basic Time Components
    # ==========================================================

    year: Optional[int] = None

    month: Optional[int] = None

    week_of_year: Optional[int] = None

    day_of_month: Optional[int] = None

    day_of_week: Optional[int] = None

    day_of_year: Optional[int] = None

    hour: Optional[int] = None

    minute: Optional[int] = None

    # ==========================================================
    # Cyclical Encoding
    # ==========================================================

    hour_sin: Optional[float] = None

    hour_cos: Optional[float] = None

    day_of_week_sin: Optional[float] = None

    day_of_week_cos: Optional[float] = None

    month_sin: Optional[float] = None

    month_cos: Optional[float] = None

    # ==========================================================
    # Trading Session
    # ==========================================================

    is_asia_session: Optional[bool] = None

    is_europe_session: Optional[bool] = None

    is_us_session: Optional[bool] = None

    session_overlap: Optional[bool] = None

    session_activity_score: Optional[float] = None

    # ==========================================================
    # Calendar Features
    # ==========================================================

    is_weekend: Optional[bool] = None

    is_month_start: Optional[bool] = None

    is_month_end: Optional[bool] = None

    is_quarter_start: Optional[bool] = None

    is_quarter_end: Optional[bool] = None

    is_year_start: Optional[bool] = None

    is_year_end: Optional[bool] = None

    # ==========================================================
    # Rolling Time Features
    # ==========================================================

    candles_from_day_start: Optional[int] = None

    candles_from_week_start: Optional[int] = None

    candles_from_month_start: Optional[int] = None

    # ==========================================================
    # Composite Time Scores
    # ==========================================================

    market_activity_score: Optional[float] = None

    seasonal_score: Optional[float] = None

    periodicity_score: Optional[float] = None

    # ==========================================================
    # Metadata
    # ==========================================================

    feature_version: str = "1.0"

    calculated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def active_session(self) -> bool:
        return (
            self.session_activity_score is not None
            and self.session_activity_score >= 0.70
        )

    @property
    def weekend_market(self) -> bool:
        return bool(self.is_weekend)

    @property
    def session_overlap_active(self) -> bool:
        return bool(self.session_overlap)

    @property
    def month_boundary(self) -> bool:
        return bool(self.is_month_start or self.is_month_end)

    @property
    def quarter_boundary(self) -> bool:
        return bool(self.is_quarter_start or self.is_quarter_end)