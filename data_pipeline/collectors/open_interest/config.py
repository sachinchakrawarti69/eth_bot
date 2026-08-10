"""
Open Interest Collector Configuration

Central configuration for the ETH futures open-interest collector.

Responsibilities:
    - Define default collection settings.
    - Define API endpoint settings.
    - Define request limits.
    - Define pagination settings.
    - Provide configuration validation.

This module does not:
    - Make API requests.
    - Parse exchange responses.
    - Validate collected records.
    - Calculate features.
    - Generate trading signals.
    - Manage trading risk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OpenInterestConfig:
    """
    Configuration for the open-interest collector.
    """

    # ------------------------------------------------------------------
    # Market
    # ------------------------------------------------------------------

    symbol: str = "ETHUSDT"

    # Default historical aggregation period.
    period: str = "1h"

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    endpoint: str = "/futures/data/openInterestHist"

    # ------------------------------------------------------------------
    # Request
    # ------------------------------------------------------------------

    limit: int = 500

    max_limit: int = 500

    # Maximum number of pages allowed during one historical request.
    max_pages: int = 100

    # ------------------------------------------------------------------
    # Timeouts
    # ------------------------------------------------------------------

    request_timeout: float = 10.0

    # ------------------------------------------------------------------
    # Collection behavior
    # ------------------------------------------------------------------

    deduplicate_records: bool = True

    normalize_timestamps: bool = True

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    validate_on_collection: bool = False

    def __post_init__(self) -> None:
        """
        Validate configuration after initialization.
        """

        self._validate_symbol()
        self._validate_period()
        self._validate_endpoint()
        self._validate_limits()
        self._validate_timeout()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_symbol(self) -> None:
        """
        Validate configured trading symbol.
        """

        if not isinstance(
            self.symbol,
            str,
        ):
            raise TypeError(
                "symbol must be a string."
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be empty."
            )

    def _validate_period(self) -> None:
        """
        Validate configured collection period.
        """

        if not isinstance(
            self.period,
            str,
        ):
            raise TypeError(
                "period must be a string."
            )

        if not self.period.strip():
            raise ValueError(
                "period cannot be empty."
            )

    def _validate_endpoint(self) -> None:
        """
        Validate API endpoint.
        """

        if not isinstance(
            self.endpoint,
            str,
        ):
            raise TypeError(
                "endpoint must be a string."
            )

        if not self.endpoint.strip():
            raise ValueError(
                "endpoint cannot be empty."
            )

        if not self.endpoint.startswith("/"):
            raise ValueError(
                "endpoint must start with '/'."
            )

    def _validate_limits(self) -> None:
        """
        Validate request and pagination limits.
        """

        if self.limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if self.max_limit <= 0:
            raise ValueError(
                "max_limit must be greater than zero."
            )

        if self.limit > self.max_limit:
            raise ValueError(
                "limit cannot exceed max_limit."
            )

        if self.max_pages <= 0:
            raise ValueError(
                "max_pages must be greater than zero."
            )

    def _validate_timeout(self) -> None:
        """
        Validate REST request timeout.
        """

        if self.request_timeout <= 0:
            raise ValueError(
                "request_timeout must be greater than zero."
            )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Return configuration as a dictionary.
        """

        return {
            "symbol": self.symbol,
            "period": self.period,
            "endpoint": self.endpoint,
            "limit": self.limit,
            "max_limit": self.max_limit,
            "max_pages": self.max_pages,
            "request_timeout": self.request_timeout,
            "deduplicate_records": (
                self.deduplicate_records
            ),
            "normalize_timestamps": (
                self.normalize_timestamps
            ),
            "validate_on_collection": (
                self.validate_on_collection
            ),
        }


DEFAULT_OPEN_INTEREST_CONFIG = OpenInterestConfig()


def get_default_config() -> OpenInterestConfig:
    """
    Return the default open-interest configuration.
    """

    return DEFAULT_OPEN_INTEREST_CONFIG


def create_config(
    *,
    symbol: str = "ETHUSDT",
    period: str = "1h",
    endpoint: str = "/futures/data/openInterestHist",
    limit: int = 500,
    max_limit: int = 500,
    max_pages: int = 100,
    request_timeout: float = 10.0,
    deduplicate_records: bool = True,
    normalize_timestamps: bool = True,
    validate_on_collection: bool = False,
) -> OpenInterestConfig:
    """
    Create a validated open-interest configuration.
    """

    return OpenInterestConfig(
        symbol=symbol,
        period=period,
        endpoint=endpoint,
        limit=limit,
        max_limit=max_limit,
        max_pages=max_pages,
        request_timeout=request_timeout,
        deduplicate_records=deduplicate_records,
        normalize_timestamps=normalize_timestamps,
        validate_on_collection=validate_on_collection,
    )