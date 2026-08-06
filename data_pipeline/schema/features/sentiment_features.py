"""
Sentiment Features Schema

Defines engineered sentiment-based features generated from
processed sentiment datasets including news, Fear & Greed,
social media, and NLP analysis.

These features are designed for machine learning models,
market regime detection, and trading strategies.

This schema stores engineered features only.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SentimentFeatureSchema:

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str
    timeframe: str
    timestamp: datetime

    # ==========================================================
    # Overall Sentiment
    # ==========================================================

    sentiment_score: Optional[float] = None
    sentiment_strength: Optional[float] = None
    sentiment_momentum: Optional[float] = None

    # ==========================================================
    # News Features
    # ==========================================================

    news_sentiment_score: Optional[float] = None
    news_volume: Optional[int] = None
    bullish_news_ratio: Optional[float] = None
    bearish_news_ratio: Optional[float] = None
    neutral_news_ratio: Optional[float] = None

    # ==========================================================
    # Fear & Greed
    # ==========================================================

    fear_greed_index: Optional[float] = None
    fear_greed_change: Optional[float] = None

    # ==========================================================
    # Social Media Features
    # ==========================================================

    social_sentiment_score: Optional[float] = None
    social_volume: Optional[int] = None
    social_engagement_score: Optional[float] = None

    # ==========================================================
    # LLM / NLP Features
    # ==========================================================

    llm_sentiment_score: Optional[float] = None
    llm_confidence: Optional[float] = None
    keyword_score: Optional[float] = None

    # ==========================================================
    # Composite Scores
    # ==========================================================

    market_sentiment_score: Optional[float] = None
    sentiment_volatility: Optional[float] = None
    sentiment_divergence: Optional[float] = None

    # ==========================================================
    # Metadata
    # ==========================================================

    feature_version: str = "1.0"
    calculated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def bullish_sentiment(self) -> bool:
        return (
            self.market_sentiment_score is not None
            and self.market_sentiment_score > 0.60
        )

    @property
    def bearish_sentiment(self) -> bool:
        return (
            self.market_sentiment_score is not None
            and self.market_sentiment_score < 0.40
        )

    @property
    def extreme_fear(self) -> bool:
        return (
            self.fear_greed_index is not None
            and self.fear_greed_index <= 20
        )

    @property
    def extreme_greed(self) -> bool:
        return (
            self.fear_greed_index is not None
            and self.fear_greed_index >= 80
        )

    @property
    def high_news_activity(self) -> bool:
        return (
            self.news_volume is not None
            and self.news_volume >= 100
        )

    @property
    def high_social_activity(self) -> bool:
        return (
            self.social_volume is not None
            and self.social_volume >= 1000
        )