"""
Processed Sentiment Schema

Defines the canonical processed sentiment data schema used by the
ETH Bot AI Trading System.

This schema is generated after processing multiple sentiment-related
raw data sources including:

- News
- Fear & Greed Index
- Social Media
- Market Sentiment
- NLP Models

The processed sentiment schema provides normalized sentiment metrics
for feature engineering, AI model training, strategy generation,
and risk management.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


SUPPORTED_SOURCES = {
    "news",
    "fear_greed",
    "social_media",
    "reddit",
    "twitter",
    "market",
}

SUPPORTED_SENTIMENT = {
    "VERY_BEARISH",
    "BEARISH",
    "NEUTRAL",
    "BULLISH",
    "VERY_BULLISH",
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
class ProcessedSentimentSchema:
    """
    Canonical processed sentiment schema.
    """

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str

    timeframe: str

    timestamp: datetime

    # ==========================================================
    # Sentiment Sources
    # ==========================================================

    news_sentiment: Optional[float] = None

    social_sentiment: Optional[float] = None

    fear_greed_index: Optional[int] = None

    market_sentiment: Optional[float] = None

    overall_sentiment_score: float = 0.0

    sentiment_label: str = "NEUTRAL"

    # ==========================================================
    # NLP Metrics
    # ==========================================================

    positive_articles: int = 0

    negative_articles: int = 0

    neutral_articles: int = 0

    total_articles: int = 0

    average_confidence: Optional[float] = None

    # ==========================================================
    # Social Metrics
    # ==========================================================

    social_mentions: Optional[int] = None

    engagement_score: Optional[float] = None

    trending_score: Optional[float] = None

    # ==========================================================
    # Processing Metadata
    # ==========================================================

    processed_at: datetime = datetime.utcnow()

    source_records: int = 0

    data_quality_score: float = 1.0

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if not self.symbol:
            raise ValueError("Symbol is required.")

        if self.timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValueError("Unsupported timeframe.")

        if self.sentiment_label not in SUPPORTED_SENTIMENT:
            raise ValueError("Invalid sentiment label.")

        if not (-1 <= self.overall_sentiment_score <= 1):
            raise ValueError(
                "Sentiment score must be between -1 and 1."
            )

        if self.fear_greed_index is not None:
            if not (0 <= self.fear_greed_index <= 100):
                raise ValueError(
                    "Fear & Greed Index must be between 0 and 100."
                )

        if self.average_confidence is not None:
            if not (0 <= self.average_confidence <= 1):
                raise ValueError(
                    "Confidence must be between 0 and 1."
                )

        if not (0 <= self.data_quality_score <= 1):
            raise ValueError(
                "Quality score must be between 0 and 1."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def bullish(self) -> bool:
        return self.overall_sentiment_score > 0

    @property
    def bearish(self) -> bool:
        return self.overall_sentiment_score < 0

    @property
    def neutral(self) -> bool:
        return self.overall_sentiment_score == 0

    @property
    def extreme_fear(self) -> bool:
        return (
            self.fear_greed_index is not None
            and self.fear_greed_index <= 25
        )

    @property
    def extreme_greed(self) -> bool:
        return (
            self.fear_greed_index is not None
            and self.fear_greed_index >= 75
        )

    @property
    def article_sentiment_ratio(self) -> float:
        if self.total_articles == 0:
            return 0.0

        return (
            self.positive_articles -
            self.negative_articles
        ) / self.total_articles

    @property
    def has_social_data(self) -> bool:
        return self.social_mentions is not None

    @property
    def has_news_data(self) -> bool:
        return self.total_articles > 0