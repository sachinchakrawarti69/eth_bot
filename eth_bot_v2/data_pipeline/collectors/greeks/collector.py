"""
Greeks Collector

Collects option Greeks market data for the ETH futures/options pipeline.

Responsibilities:
    - Request Greeks data from the configured exchange/API client.
    - Collect raw Greeks responses.
    - Handle request timeouts and transient failures.
    - Apply retry logic.
    - Attach collection metadata.
    - Return raw responses to the parser.

This module does not:
    - Parse exchange responses.
    - Validate normalized records.
    - Calculate Greeks.
    - Calculate implied volatility.
    - Generate indicators.
    - Generate ML features.
    - Generate trading signals.
    - Perform risk management.
    - Execute trades.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Protocol


logger = logging.getLogger(__name__)


class GreeksCollectorError(RuntimeError):
    """Base exception for Greeks collector failures."""


class GreeksCollectorConfigurationError(
    GreeksCollectorError
):
    """Raised when collector configuration is invalid."""


class GreeksCollectorRequestError(
    GreeksCollectorError
):
    """Raised when a Greeks API request fails."""


class GreeksCollectorResponseError(
    GreeksCollectorError
):
    """Raised when an exchange returns an unusable response."""


class GreeksAPIClient(Protocol):
    """
    Minimal API-client interface required by the collector.

    A concrete exchange client should implement this method.
    """

    def get_greeks(
        self,
        *,
        symbol: Optional[str] = None,
        expiry: Optional[str] = None,
        strike: Optional[float] = None,
        option_type: Optional[str] = None,
    ) -> Any:
        ...


@dataclass(frozen=True, slots=True)
class GreeksCollectorConfig:
    """
    Runtime configuration for the Greeks collector.
    """

    symbol: Optional[str] = None
    expiry: Optional[str] = None
    strike: Optional[float] = None
    option_type: Optional[str] = None

    timeout_seconds: float = 10.0

    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    retry_backoff_factor: float = 2.0

    jitter_seconds: float = 0.25

    fail_on_empty_response: bool = True

    def validate(self) -> None:
        """Validate collector configuration."""

        if self.timeout_seconds <= 0:
            raise GreeksCollectorConfigurationError(
                "timeout_seconds must be greater than zero"
            )

        if self.max_retries < 0:
            raise GreeksCollectorConfigurationError(
                "max_retries cannot be negative"
            )

        if self.retry_delay_seconds < 0:
            raise GreeksCollectorConfigurationError(
                "retry_delay_seconds cannot be negative"
            )

        if self.retry_backoff_factor < 1:
            raise GreeksCollectorConfigurationError(
                "retry_backoff_factor must be >= 1"
            )

        if self.jitter_seconds < 0:
            raise GreeksCollectorConfigurationError(
                "jitter_seconds cannot be negative"
            )

        if self.strike is not None and self.strike <= 0:
            raise GreeksCollectorConfigurationError(
                "strike must be greater than zero"
            )

        if self.option_type is not None:
            normalized = self.option_type.upper()

            if normalized not in {"CALL", "PUT", "C", "P"}:
                raise GreeksCollectorConfigurationError(
                    "option_type must be CALL, PUT, C, or P"
                )


@dataclass(frozen=True, slots=True)
class GreeksRawResponse:
    """
    Raw response returned by the Greeks collector.

    The collector deliberately preserves the exchange response
    without transforming its schema.
    """

    data: Any
    collected_at: int
    symbol: Optional[str]
    expiry: Optional[str]
    strike: Optional[float]
    option_type: Optional[str]

    attempt: int
    source: str


class GreeksCollector:
    """
    Collects raw option Greeks data.

    The collector is exchange/API agnostic. The concrete API client
    is injected into the constructor.
    """

    def __init__(
        self,
        client: GreeksAPIClient,
        config: Optional[GreeksCollectorConfig] = None,
        *,
        source: str = "exchange",
    ) -> None:
        if client is None:
            raise GreeksCollectorConfigurationError(
                "client is required"
            )

        self.client = client

        self.config = (
            config
            if config is not None
            else GreeksCollectorConfig()
        )

        self.config.validate()

        if not source.strip():
            raise GreeksCollectorConfigurationError(
                "source cannot be empty"
            )

        self.source = source.strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect(self) -> GreeksRawResponse:
        """
        Collect Greeks data.

        Returns:
            GreeksRawResponse

        Raises:
            GreeksCollectorRequestError
            GreeksCollectorResponseError
        """

        last_error: Optional[Exception] = None

        total_attempts = self.config.max_retries + 1

        for attempt in range(1, total_attempts + 1):
            try:
                logger.debug(
                    "Collecting Greeks data "
                    "(attempt %s/%s)",
                    attempt,
                    total_attempts,
                )

                raw_response = self._request()

                self._validate_response(
                    raw_response
                )

                collected_at = self._current_timestamp_ms()

                return GreeksRawResponse(
                    data=raw_response,
                    collected_at=collected_at,
                    symbol=self.config.symbol,
                    expiry=self.config.expiry,
                    strike=self.config.strike,
                    option_type=self._normalize_option_type(
                        self.config.option_type
                    ),
                    attempt=attempt,
                    source=self.source,
                )

            except (
                TimeoutError,
                ConnectionError,
                OSError,
            ) as exc:
                last_error = exc

                logger.warning(
                    "Transient Greeks collection "
                    "failure on attempt %s/%s: %s",
                    attempt,
                    total_attempts,
                    exc,
                )

                if attempt < total_attempts:
                    self._sleep_before_retry(
                        attempt
                    )

            except GreeksCollectorError:
                raise

            except Exception as exc:
                last_error = exc

                logger.exception(
                    "Unexpected Greeks collection "
                    "failure on attempt %s/%s",
                    attempt,
                    total_attempts,
                )

                if attempt < total_attempts:
                    self._sleep_before_retry(
                        attempt
                    )

        raise GreeksCollectorRequestError(
            "Failed to collect Greeks data after "
            f"{total_attempts} attempts"
        ) from last_error

    def collect_data(self) -> Any:
        """
        Collect and return only the raw API payload.

        This method is useful when metadata is handled by the
        surrounding pipeline.
        """

        result = self.collect()

        return result.data

    def collect_many(
        self,
        symbols: list[str],
    ) -> list[GreeksRawResponse]:
        """
        Collect Greeks data for multiple symbols.

        Each symbol is collected independently.

        Raises:
            GreeksCollectorRequestError
            GreeksCollectorResponseError
        """

        responses: list[GreeksRawResponse] = []

        for symbol in symbols:
            normalized_symbol = self._normalize_symbol(
                symbol
            )

            collector_config = GreeksCollectorConfig(
                symbol=normalized_symbol,
                expiry=self.config.expiry,
                strike=self.config.strike,
                option_type=self.config.option_type,
                timeout_seconds=self.config.timeout_seconds,
                max_retries=self.config.max_retries,
                retry_delay_seconds=(
                    self.config.retry_delay_seconds
                ),
                retry_backoff_factor=(
                    self.config.retry_backoff_factor
                ),
                jitter_seconds=self.config.jitter_seconds,
                fail_on_empty_response=(
                    self.config.fail_on_empty_response
                ),
            )

            collector = GreeksCollector(
                client=self.client,
                config=collector_config,
                source=self.source,
            )

            responses.append(
                collector.collect()
            )

        return responses

    # ------------------------------------------------------------------
    # Request
    # ------------------------------------------------------------------

    def _request(self) -> Any:
        """
        Execute the underlying API request.
        """

        kwargs: dict[str, Any] = {
            "symbol": self.config.symbol,
            "expiry": self.config.expiry,
            "strike": self.config.strike,
            "option_type": self._normalize_option_type(
                self.config.option_type
            ),
        }

        try:
            return self.client.get_greeks(
                **kwargs
            )

        except TypeError as exc:
            raise GreeksCollectorRequestError(
                "Greeks API client does not support "
                "the required get_greeks interface"
            ) from exc

        except TimeoutError:
            raise

        except ConnectionError:
            raise

        except OSError:
            raise

        except Exception as exc:
            raise GreeksCollectorRequestError(
                "Greeks API request failed"
            ) from exc

    # ------------------------------------------------------------------
    # Response Validation
    # ------------------------------------------------------------------

    def _validate_response(
        self,
        response: Any,
    ) -> None:
        """
        Perform minimal response-level checks.

        Detailed schema validation belongs to validator.py.
        """

        if response is None:
            raise GreeksCollectorResponseError(
                "Greeks API returned None"
            )

        if (
            self.config.fail_on_empty_response
            and self._is_empty_response(response)
        ):
            raise GreeksCollectorResponseError(
                "Greeks API returned an empty response"
            )

    @staticmethod
    def _is_empty_response(
        response: Any,
    ) -> bool:
        """
        Detect common empty API responses.
        """

        if isinstance(
            response,
            (list, tuple, set, frozenset),
        ):
            return len(response) == 0

        if isinstance(
            response,
            Mapping,
        ):
            return len(response) == 0

        if isinstance(
            response,
            str,
        ):
            return not response.strip()

        return False

    # ------------------------------------------------------------------
    # Retry Handling
    # ------------------------------------------------------------------

    def _sleep_before_retry(
        self,
        attempt: int,
    ) -> None:
        """
        Apply exponential backoff with optional jitter.
        """

        delay = (
            self.config.retry_delay_seconds
            * (
                self.config.retry_backoff_factor
                ** (attempt - 1)
            )
        )

        if self.config.jitter_seconds > 0:
            delay += random.uniform(
                0,
                self.config.jitter_seconds,
            )

        logger.debug(
            "Waiting %.3f seconds before "
            "Greeks retry",
            delay,
        )

        time.sleep(delay)

    # ------------------------------------------------------------------
    # Normalization Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_symbol(
        symbol: Optional[str],
    ) -> Optional[str]:
        """
        Normalize an optional symbol.
        """

        if symbol is None:
            return None

        if not isinstance(symbol, str):
            raise GreeksCollectorConfigurationError(
                "symbol must be a string"
            )

        normalized = symbol.strip().upper()

        if not normalized:
            raise GreeksCollectorConfigurationError(
                "symbol cannot be empty"
            )

        return normalized

    @staticmethod
    def _normalize_option_type(
        option_type: Optional[str],
    ) -> Optional[str]:
        """
        Normalize option type.

        Supported inputs:
            CALL
            PUT
            C
            P
        """

        if option_type is None:
            return None

        if not isinstance(option_type, str):
            raise GreeksCollectorConfigurationError(
                "option_type must be a string"
            )

        normalized = option_type.strip().upper()

        mapping = {
            "C": "CALL",
            "CALL": "CALL",
            "P": "PUT",
            "PUT": "PUT",
        }

        if normalized not in mapping:
            raise GreeksCollectorConfigurationError(
                "option_type must be CALL, PUT, C, or P"
            )

        return mapping[normalized]

    # ------------------------------------------------------------------
    # Time
    # ------------------------------------------------------------------

    @staticmethod
    def _current_timestamp_ms() -> int:
        """
        Return current UTC timestamp in milliseconds.
        """

        return int(
            datetime.now(
                timezone.utc
            ).timestamp()
            * 1000
        )


# ----------------------------------------------------------------------
# Convenience Functions
# ----------------------------------------------------------------------

def collect_greeks(
    client: GreeksAPIClient,
    config: Optional[GreeksCollectorConfig] = None,
    *,
    source: str = "exchange",
) -> GreeksRawResponse:
    """
    Collect raw Greeks data using a temporary collector.
    """

    collector = GreeksCollector(
        client=client,
        config=config,
        source=source,
    )

    return collector.collect()


def collect_greeks_data(
    client: GreeksAPIClient,
    config: Optional[GreeksCollectorConfig] = None,
    *,
    source: str = "exchange",
) -> Any:
    """
    Collect and return only the raw Greeks payload.
    """

    result = collect_greeks(
        client=client,
        config=config,
        source=source,
    )

    return result.data