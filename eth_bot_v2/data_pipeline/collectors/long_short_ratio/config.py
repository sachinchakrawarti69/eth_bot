"""
Long/Short Ratio Collector Configuration

Central configuration for the ETH futures long/short ratio collector.

Responsibilities:
    - Define collector defaults.
    - Define supported periods.
    - Define API request limits.
    - Define timeout and retry settings.
    - Define symbol configuration.
    - Keep configuration separate from collection logic.

This module does not:
    - Collect data.
    - Parse exchange responses.
    - Validate records.
    - Calculate indicators.
    - Generate trading signals.
    - Manage risk.
    - Execute trades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


# ============================================================================
# Core Defaults
# ============================================================================

DEFAULT_SYMBOL: Final[str] = "ETHUSDT"

DEFAULT_PERIOD: Final[str] = "5m"

DEFAULT_LIMIT: Final[int] = 500

MIN_LIMIT: Final[int] = 1

MAX_LIMIT: Final[int] = 500

DEFAULT_TIMEOUT_SECONDS: Final[float] = 10.0


# ============================================================================
# Supported Periods
# ============================================================================

SUPPORTED_PERIODS: Final[frozenset[str]] = frozenset(
    {
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "12h",
        "1d",
    }
)


# ============================================================================
# API Configuration
# ============================================================================

@dataclass(frozen=True, slots=True)
class LongShortRatioAPIConfig:
    """
    Exchange API configuration for long/short ratio collection.
    """

    endpoint: str = (
        "/futures/data/globalLongShortAccountRatio"
    )

    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    max_retries: int = 3

    retry_backoff_seconds: float = 1.0

    rate_limit_requests_per_minute: int = 120


# ============================================================================
# Collection Configuration
# ============================================================================

@dataclass(frozen=True, slots=True)
class LongShortRatioCollectionConfig:
    """
    Main configuration for long/short ratio collection.

    The configuration is immutable so runtime collection code cannot
    accidentally modify shared settings.
    """

    symbol: str = DEFAULT_SYMBOL

    period: str = DEFAULT_PERIOD

    limit: int = DEFAULT_LIMIT

    supported_periods: frozenset[str] = field(
        default_factory=lambda: SUPPORTED_PERIODS
    )

    min_limit: int = MIN_LIMIT

    max_limit: int = MAX_LIMIT

    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    enable_pagination: bool = True

    page_size: int = DEFAULT_LIMIT

    stop_on_short_page: bool = True

    stop_on_empty_page: bool = True

    pagination_timestamp_increment: int = 1


# ============================================================================
# Historical Collection Configuration
# ============================================================================

@dataclass(frozen=True, slots=True)
class LongShortRatioHistoricalConfig:
    """
    Configuration for historical long/short ratio collection.
    """

    enabled: bool = True

    batch_size: int = DEFAULT_LIMIT

    max_pages: int = 10_000

    require_monotonic_timestamps: bool = True

    allow_duplicate_timestamps: bool = False


# ============================================================================
# Validation Configuration
# ============================================================================

@dataclass(frozen=True, slots=True)
class LongShortRatioValidationConfig:
    """
    Configuration used by downstream long/short ratio validation.

    This class defines validation policy only. Actual validation is
    implemented by validator.py.
    """

    expected_symbol: str = DEFAULT_SYMBOL

    require_symbol: bool = True

    require_period: bool = True

    require_timestamp: bool = True

    require_long_account: bool = True

    require_short_account: bool = True

    require_long_short_ratio: bool = True

    allow_zero_long_account: bool = True

    allow_zero_short_account: bool = True

    require_finite_numbers: bool = True

    reject_negative_accounts: bool = True

    reject_negative_ratio: bool = True


# ============================================================================
# Storage Configuration
# ============================================================================

@dataclass(frozen=True, slots=True)
class LongShortRatioStorageConfig:
    """
    Storage configuration for collected long/short ratio data.
    """

    dataset_name: str = "long_short_ratio"

    raw_subdirectory: str = "long_short_ratio"

    file_format: str = "parquet"

    partition_by_symbol: bool = True

    partition_by_date: bool = True

    compression: str = "snappy"


# ============================================================================
# Monitoring Configuration
# ============================================================================

@dataclass(frozen=True, slots=True)
class LongShortRatioMonitoringConfig:
    """
    Monitoring configuration for the collector.
    """

    enabled: bool = True

    log_requests: bool = True

    log_response_size: bool = True

    log_latency: bool = True

    alert_on_empty_response: bool = True

    alert_on_repeated_failure: bool = True

    failure_threshold: int = 5


# ============================================================================
# Complete Configuration
# ============================================================================

@dataclass(frozen=True, slots=True)
class LongShortRatioConfig:
    """
    Complete long/short ratio collector configuration.
    """

    collection: LongShortRatioCollectionConfig = field(
        default_factory=LongShortRatioCollectionConfig
    )

    api: LongShortRatioAPIConfig = field(
        default_factory=LongShortRatioAPIConfig
    )

    historical: LongShortRatioHistoricalConfig = field(
        default_factory=LongShortRatioHistoricalConfig
    )

    validation: LongShortRatioValidationConfig = field(
        default_factory=LongShortRatioValidationConfig
    )

    storage: LongShortRatioStorageConfig = field(
        default_factory=LongShortRatioStorageConfig
    )

    monitoring: LongShortRatioMonitoringConfig = field(
        default_factory=LongShortRatioMonitoringConfig
    )


# ============================================================================
# Default Configuration
# ============================================================================

DEFAULT_CONFIG: Final[LongShortRatioConfig] = (
    LongShortRatioConfig()
)


# ============================================================================
# Configuration Helpers
# ============================================================================

def normalize_symbol(
    symbol: str,
) -> str:
    """
    Normalize a futures symbol.
    """

    if not isinstance(symbol, str):
        raise TypeError(
            "symbol must be a string."
        )

    normalized = symbol.strip().upper()

    if not normalized:
        raise ValueError(
            "symbol cannot be empty."
        )

    return normalized


def normalize_period(
    period: str,
) -> str:
    """
    Normalize and validate the collection period.
    """

    if not isinstance(period, str):
        raise TypeError(
            "period must be a string."
        )

    normalized = period.strip().lower()

    if normalized not in SUPPORTED_PERIODS:
        raise ValueError(
            "Unsupported period "
            f"'{period}'. Supported periods: "
            f"{sorted(SUPPORTED_PERIODS)}"
        )

    return normalized


def validate_limit(
    limit: int,
) -> int:
    """
    Validate API request limit.
    """

    if isinstance(limit, bool):
        raise TypeError(
            "limit must be an integer."
        )

    if not isinstance(limit, int):
        raise TypeError(
            "limit must be an integer."
        )

    if not (
        MIN_LIMIT
        <= limit
        <= MAX_LIMIT
    ):
        raise ValueError(
            f"limit must be between "
            f"{MIN_LIMIT} and {MAX_LIMIT}."
        )

    return limit


def create_config(
    *,
    symbol: str = DEFAULT_SYMBOL,
    period: str = DEFAULT_PERIOD,
    limit: int = DEFAULT_LIMIT,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    enable_pagination: bool = True,
) -> LongShortRatioConfig:
    """
    Create a validated long/short ratio configuration.
    """

    normalized_symbol = normalize_symbol(
        symbol
    )

    normalized_period = normalize_period(
        period
    )

    validated_limit = validate_limit(
        limit
    )

    if isinstance(
        timeout_seconds,
        bool,
    ):
        raise TypeError(
            "timeout_seconds must be numeric."
        )

    if not isinstance(
        timeout_seconds,
        (int, float),
    ):
        raise TypeError(
            "timeout_seconds must be numeric."
        )

    if timeout_seconds <= 0:
        raise ValueError(
            "timeout_seconds must be greater than zero."
        )

    if not isinstance(
        enable_pagination,
        bool,
    ):
        raise TypeError(
            "enable_pagination must be a boolean."
        )

    collection = LongShortRatioCollectionConfig(
        symbol=normalized_symbol,
        period=normalized_period,
        limit=validated_limit,
        supported_periods=SUPPORTED_PERIODS,
        min_limit=MIN_LIMIT,
        max_limit=MAX_LIMIT,
        timeout_seconds=float(
            timeout_seconds
        ),
        enable_pagination=enable_pagination,
        page_size=validated_limit,
    )

    api = LongShortRatioAPIConfig(
        timeout_seconds=float(
            timeout_seconds
        )
    )

    validation = LongShortRatioValidationConfig(
        expected_symbol=normalized_symbol
    )

    return LongShortRatioConfig(
        collection=collection,
        api=api,
        validation=validation,
    )