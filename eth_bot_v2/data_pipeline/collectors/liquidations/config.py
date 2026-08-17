"""
Liquidations Collector Configuration

Configuration for collecting ETH futures liquidation data.

Responsibilities:
    - Define API endpoint.
    - Define trading symbol.
    - Define request limits.
    - Define timeout.
    - Define pagination limits.
    - Define deduplication behavior.

This module does not:
    - Make API requests.
    - Parse responses.
    - Validate liquidation records.
    - Calculate indicators.
    - Generate trading signals.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LiquidationCollectorConfig:
    """
    Configuration for the liquidation collector.

    All timestamps used by the collector are Unix milliseconds.
    """

    # --------------------------------------------------------------
    # Instrument
    # --------------------------------------------------------------

    symbol: str = "ETHUSDT"

    # --------------------------------------------------------------
    # API
    # --------------------------------------------------------------

    endpoint: str = "/futures/data/allForceOrders"

    request_timeout: float = 10.0

    # --------------------------------------------------------------
    # Request limits
    # --------------------------------------------------------------

    limit: int = 100

    max_limit: int = 1000

    # --------------------------------------------------------------
    # Historical pagination
    # --------------------------------------------------------------

    max_pages: int = 100

    # --------------------------------------------------------------
    # Data handling
    # --------------------------------------------------------------

    deduplicate_records: bool = True

    def __post_init__(self) -> None:
        """Validate configuration values."""

        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be empty."
            )

        if not isinstance(self.endpoint, str):
            raise TypeError(
                "endpoint must be a string."
            )

        if not self.endpoint.strip():
            raise ValueError(
                "endpoint cannot be empty."
            )

        if isinstance(self.request_timeout, bool):
            raise TypeError(
                "request_timeout must be numeric."
            )

        if self.request_timeout <= 0:
            raise ValueError(
                "request_timeout must be greater than zero."
            )

        if isinstance(self.limit, bool):
            raise TypeError(
                "limit must be an integer."
            )

        if not isinstance(self.limit, int):
            raise TypeError(
                "limit must be an integer."
            )

        if self.limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if isinstance(self.max_limit, bool):
            raise TypeError(
                "max_limit must be an integer."
            )

        if not isinstance(self.max_limit, int):
            raise TypeError(
                "max_limit must be an integer."
            )

        if self.max_limit <= 0:
            raise ValueError(
                "max_limit must be greater than zero."
            )

        if self.limit > self.max_limit:
            raise ValueError(
                "limit cannot exceed max_limit."
            )

        if isinstance(self.max_pages, bool):
            raise TypeError(
                "max_pages must be an integer."
            )

        if not isinstance(self.max_pages, int):
            raise TypeError(
                "max_pages must be an integer."
            )

        if self.max_pages <= 0:
            raise ValueError(
                "max_pages must be greater than zero."
            )

        if not isinstance(
            self.deduplicate_records,
            bool,
        ):
            raise TypeError(
                "deduplicate_records must be a boolean."
            )


DEFAULT_LIQUIDATION_CONFIG = LiquidationCollectorConfig()