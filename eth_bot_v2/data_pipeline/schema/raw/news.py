"""
Raw News Schema

Defines the canonical schema for cryptocurrency news collected from
news providers, RSS feeds, market intelligence platforms, and social
media sources.

This schema represents news in its raw form before NLP processing,
sentiment analysis, entity extraction, summarization, or feature
engineering.

All provider-specific news responses should be normalized into this
schema before validation and processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


SUPPORTED_SOURCES = {
    "COINDESK",
    "COINTELEGRAPH",
    "THE_BLOCK",
    "DECRYPT",
    "BINANCE",
    "BYBIT",
    "OKX",
    "RSS",
    "TWITTER",
    "REDDIT",
    "CUSTOM",
}

SUPPORTED_CATEGORIES = {
    "MARKET",
    "MACRO",
    "REGULATION",
    "EXCHANGE",
    "BLOCKCHAIN",
    "DEFI",
    "NFT",
    "SECURITY",
    "HACK",
    "MINING",
    "ONCHAIN",
    "AI",
    "GENERAL",
}

SUPPORTED_LANGUAGES = {
    "en",
    "es",
    "fr",
    "de",
    "ja",
    "ko",
    "zh",
    "hi",
}


@dataclass
class NewsSchema:
    """
    Canonical raw news schema.
    """

    # ==========================================================
    # Source Information
    # ==========================================================

    source: str

    provider: str

    source_url: str

    article_url: str

    # ==========================================================
    # Article Information
    # ==========================================================

    article_id: str

    title: str

    summary: Optional[str] = None

    content: Optional[str] = None

    author: Optional[str] = None

    category: str = "GENERAL"

    language: str = "en"

    # ==========================================================
    # Time Information
    # ==========================================================

    published_at: datetime

    received_at: datetime

    updated_at: Optional[datetime] = None

    # ==========================================================
    # Asset Information
    # ==========================================================

    assets: Optional[List[str]] = None

    symbols: Optional[List[str]] = None

    tags: Optional[List[str]] = None

    # ==========================================================
    # Metadata
    # ==========================================================

    image_url: Optional[str] = None

    sentiment_score: Optional[float] = None

    importance_score: Optional[float] = None

    duplicate_of: Optional[str] = None

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        if self.source not in SUPPORTED_SOURCES:
            raise ValueError(
                f"Unsupported source: {self.source}"
            )

        if not self.provider:
            raise ValueError(
                "Provider is required."
            )

        if not self.source_url:
            raise ValueError(
                "Source URL is required."
            )

        if not self.article_url:
            raise ValueError(
                "Article URL is required."
            )

        if not self.article_id:
            raise ValueError(
                "Article ID is required."
            )

        if not self.title:
            raise ValueError(
                "Title is required."
            )

        if self.category not in SUPPORTED_CATEGORIES:
            raise ValueError(
                f"Unsupported category: {self.category}"
            )

        if self.language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {self.language}"
            )

        if self.published_at is None:
            raise ValueError(
                "Published time is required."
            )

        if self.received_at is None:
            raise ValueError(
                "Received time is required."
            )

        if (
            self.sentiment_score is not None
            and not (-1.0 <= self.sentiment_score <= 1.0)
        ):
            raise ValueError(
                "Sentiment score must be between -1 and 1."
            )

        if (
            self.importance_score is not None
            and not (0.0 <= self.importance_score <= 1.0)
        ):
            raise ValueError(
                "Importance score must be between 0 and 1."
            )

        return True

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def has_summary(self) -> bool:
        return self.summary is not None

    @property
    def has_content(self) -> bool:
        return self.content is not None

    @property
    def is_duplicate(self) -> bool:
        return self.duplicate_of is not None

    @property
    def has_sentiment(self) -> bool:
        return self.sentiment_score is not None

    @property
    def bullish(self) -> bool:
        return (
            self.sentiment_score is not None
            and self.sentiment_score > 0
        )

    @property
    def bearish(self) -> bool:
        return (
            self.sentiment_score is not None
            and self.sentiment_score < 0
        )

    @property
    def neutral(self) -> bool:
        return (
            self.sentiment_score is not None
            and self.sentiment_score == 0
        )