
"""
Funding Rate Collector Configuration

Central configuration for the funding-rate collector.

Responsibilities:
    - Define funding-rate collection defaults.
    - Define API request limits.
    - Define pagination limits.
    - Define retry-related settings.
    - Define collection behavior.

This module does not:
    - Collect data.
    - Parse API responses.
    - Validate records.
    - Calculate funding-rate features.
    - Execute trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FundingRateConfig:
    """
    Configuration for the funding-rate collector.
    """

    # ==========================================================
    # Market
    # ==========================================================

    symbol: str = "ETHUSDT"

    # ==========================================================
    # API Request
    # ==========================================================

    limit: int = 1000

    # Maximum number of pages allowed for one historical request.
    max_pages: int = 100

    # ==========================================================
    # Collection
    # ==========================================================

    # Whether historical collection is enabled.
    enable_historical: bool = True

    # Whether latest funding-rate collection is enabled.
    enable_latest: bool = True

    # ==========================================================
    # Time Handling
    # ==========================================================

    # All timestamps exchanged with the collector are expected
    # to use Unix milliseconds.
    timestamp_unit: str = "ms"

    # ==========================================================
    # Retry
    # ==========================================================

    max_retries: int = 5

    retry_delay_seconds: float = 1.0

    retry_backoff_factor: float = 2.0

    # ==========================================================
    # Request Timeout
    # ==========================================================

    timeout_seconds: float = 10.0

    # ==========================================================
    # Rate Limiting
    # ==========================================================

    requests_per_second: Optional[float] = None

    # ==========================================================
    # Validation
    # ==========================================================

    validate_symbol: bool = True

    validate_time_range: bool = True

    # ==========================================================
    # Runtime
    # ==========================================================

    enabled: bool = True

    # ==========================================================
    # Configuration Validation
    # ==========================================================

    def __post_init__(self) -> None:
        """
        Validate configuration at construction time.
        """

        if not self.symbol.strip():
            raise ValueError(
                "Funding-rate symbol cannot be empty."
            )

        if self.limit <= 0:
            raise ValueError(
                "Funding-rate limit must be greater than zero."
            )

        if self.limit > 1000:
            raise ValueError(
                "Funding-rate limit cannot exceed 1000."
            )

        if self.max_pages <= 0:
            raise ValueError(
                "max_pages must be greater than zero."
            )

        if self.max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative."
            )

        if self.retry_delay_seconds < 0:
            raise ValueError(
                "retry_delay_seconds cannot be negative."
            )

        if self.retry_backoff_factor < 1:
            raise ValueError(
                "retry_backoff_factor must be at least 1."
            )

        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

        if self.timestamp_unit != "ms":
            raise ValueError(
                "Funding-rate timestamps must use "
                "Unix milliseconds."
            )

        if (
            self.requests_per_second is not None
            and self.requests_per_second <= 0
        ):
            raise ValueError(
                "requests_per_second must be greater "
                "than zero when provided."
            )


# ==============================================================
# Default Configuration
# ==============================================================

DEFAULT_FUNDING_RATE_CONFIG = FundingRateConfig()


# ==============================================================
# Configuration Factory
# ==============================================================

def get_funding_rate_config(
    *,
    symbol: Optional[str] = None,
) -> FundingRateConfig:
    """
    Return the default funding-rate configuration.

    Parameters
    ----------
    symbol:
        Optional futures symbol override.

    Returns
    -------
    FundingRateConfig
        Immutable collector configuration.
    """

    if symbol is None:
        return DEFAULT_FUNDING_RATE_CONFIG

    return FundingRateConfig(
        symbol=symbol,
        limit=DEFAULT_FUNDING_RATE_CONFIG.limit,
        max_pages=DEFAULT_FUNDING_RATE_CONFIG.max_pages,
        enable_historical=(
            DEFAULT_FUNDING_RATE_CONFIG.enable_historical
        ),
        enable_latest=(
            DEFAULT_FUNDING_RATE_CONFIG.enable_latest
        ),
        timestamp_unit=(
            DEFAULT_FUNDING_RATE_CONFIG.timestamp_unit
        ),
        max_retries=(
            DEFAULT_FUNDING_RATE_CONFIG.max_retries
        ),
        retry_delay_seconds=(
            DEFAULT_FUNDING_RATE_CONFIG.retry_delay_seconds
        ),
        retry_backoff_factor=(
            DEFAULT_FUNDING_RATE_CONFIG.retry_backoff_factor
        ),
        timeout_seconds=(
            DEFAULT_FUNDING_RATE_CONFIG.timeout_seconds
        ),
        requests_per_second=(
            DEFAULT_FUNDING_RATE_CONFIG.requests_per_second
        ),
        validate_symbol=(
            DEFAULT_FUNDING_RATE_CONFIG.validate_symbol
        ),
        validate_time_range=(
            DEFAULT_FUNDING_RATE_CONFIG.validate_time_range
        ),
        enabled=(
            DEFAULT_FUNDING_RATE_CONFIG.enabled
        ),
    )
