"""
Derivative Features Schema

Defines engineered derivative-market features generated from
processed futures and options data.

These features summarize futures positioning, leverage,
funding conditions, liquidation activity, and options
market behavior for machine learning models.

This schema stores engineered features only.
Feature calculations are performed by the Feature Engineering Pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DerivativeFeatureSchema:

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str

    timeframe: str

    timestamp: datetime

    # ==========================================================
    # Open Interest Features
    # ==========================================================

    open_interest: Optional[float] = None

    open_interest_change: Optional[float] = None

    open_interest_percent_change: Optional[float] = None

    open_interest_zscore: Optional[float] = None

    # ==========================================================
    # Funding Rate Features
    # ==========================================================

    funding_rate: Optional[float] = None

    funding_rate_change: Optional[float] = None

    cumulative_funding: Optional[float] = None

    funding_bias_score: Optional[float] = None

    # ==========================================================
    # Long / Short Features
    # ==========================================================

    long_short_ratio: Optional[float] = None

    long_account_ratio: Optional[float] = None

    short_account_ratio: Optional[float] = None

    long_short_change: Optional[float] = None

    # ==========================================================
    # Liquidation Features
    # ==========================================================

    long_liquidation_volume: Optional[float] = None

    short_liquidation_volume: Optional[float] = None

    liquidation_imbalance: Optional[float] = None

    liquidation_spike_score: Optional[float] = None

    # ==========================================================
    # Options Features
    # ==========================================================

    implied_volatility: Optional[float] = None

    iv_percentile: Optional[float] = None

    put_call_ratio: Optional[float] = None

    options_volume: Optional[float] = None

    options_open_interest: Optional[float] = None

    # ==========================================================
    # Greeks Features
    # ==========================================================

    delta_exposure: Optional[float] = None

    gamma_exposure: Optional[float] = None

    vega_exposure: Optional[float] = None

    theta_exposure: Optional[float] = None

    # ==========================================================
    # Composite Features
    # ==========================================================

    leverage_score: Optional[float] = None

    derivatives_sentiment_score: Optional[float] = None

    squeeze_probability: Optional[float] = None

    market_stress_score: Optional[float] = None

    # ==========================================================
    # Metadata
    # ==========================================================

    feature_version: str = "1.0"

    calculated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def bullish_funding(self) -> bool:
        return (
            self.funding_rate is not None
            and self.funding_rate > 0
        )

    @property
    def bearish_funding(self) -> bool:
        return (
            self.funding_rate is not None
            and self.funding_rate < 0
        )

    @property
    def high_leverage(self) -> bool:
        return (
            self.leverage_score is not None
            and self.leverage_score >= 0.80
        )

    @property
    def short_squeeze_risk(self) -> bool:
        return (
            self.squeeze_probability is not None
            and self.squeeze_probability >= 0.70
        )

    @property
    def stressed_market(self) -> bool:
        return (
            self.market_stress_score is not None
            and self.market_stress_score >= 0.75
        )