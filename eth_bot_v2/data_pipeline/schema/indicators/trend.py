"""
Trend Technical Indicators Schema

Stores calculated trend indicators produced by the
Technical Indicator Engine.

These indicators are generated from processed market
data and later consumed by Feature Engineering,
Dataset Builder, and AI models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TrendIndicatorSchema:

    # ==========================================
    # Asset Information
    # ==========================================

    symbol: str

    timeframe: str

    timestamp: datetime

    # ==========================================
    # Moving Averages
    # ==========================================

    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_100: Optional[float] = None
    sma_200: Optional[float] = None

    ema_9: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_100: Optional[float] = None
    ema_200: Optional[float] = None

    # ==========================================
    # MACD
    # ==========================================

    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None

    # ==========================================
    # Trend Strength
    # ==========================================

    adx: Optional[float] = None

    plus_di: Optional[float] = None

    minus_di: Optional[float] = None

    # ==========================================
    # Ichimoku
    # ==========================================

    tenkan_sen: Optional[float] = None

    kijun_sen: Optional[float] = None

    senkou_span_a: Optional[float] = None

    senkou_span_b: Optional[float] = None

    chikou_span: Optional[float] = None

    # ==========================================
    # Parabolic SAR
    # ==========================================

    parabolic_sar: Optional[float] = None

    # ==========================================
    # Metadata
    # ==========================================

    indicator_version: str = "1.0"

    calculated_at: Optional[datetime] = None