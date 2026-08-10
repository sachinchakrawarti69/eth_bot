"""
Option Chain Collector

Collects ETH futures/options chain market data from an exchange REST API.

Responsibilities:
    - Request option-chain data.
    - Handle pagination when supported.
    - Apply collector configuration.
    - Retry transient failures.
    - Return raw exchange responses to the parser.

This module does not:
    - Parse exchange-specific response fields.
    - Validate normalized records.
    - Calculate Greeks.
    - Calculate implied volatility.
    - Generate indicators/features.
    - Generate trading signals.
    - Perform risk management.
    - Execute trades.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import requests


@dataclass(frozen=True, slots=True)
class OptionChainCollectorConfig:
    """
    Configuration for the option-chain collector.
    """

    base_url: str = "https://eapi.binance.com"

    endpoint: str = "/eapi/v1/exchangeInfo"

    symbol: str = "ETH"

    timeout: float = 10.0

    max_retries: int = 3

    retry_delay: float = 1.0

    backoff_factor: float = 2.0

    enabled: bool = True

    verify_ssl: bool = True

    user_agent: str = "eth-bot-option-chain-collector/1.0"


@dataclass(frozen=True, slots=True)
class CollectionResult:
    """
    Result returned by the option-chain collector.
    """

    success: bool

    data: Any = None

    status_code: Optional[int] = None

    error: Optional[str] = None

    attempts: int = 0


class OptionChainCollector:
    """
    Collects raw ETH option-chain data.

    The collector intentionally returns raw exchange data.
    Parsing and normalization belong to parser.py.
    """

    RETRYABLE_STATUS_CODES = frozenset(
        {
            408,
            425,
            429,
            500,
            502,
            503,
            504,
        }
    )

    def __init__(
        self,
        config: Optional[
            OptionChainCollectorConfig
        ] = None,
        session: Optional[
            requests.Session
        ] = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else OptionChainCollectorConfig()
        )

        self.session = (
            session
            if session is not None
            else requests.Session()
        )

        self._validate_config()

        self.session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect(self) -> CollectionResult:
        """
        Collect the configured ETH option-chain response.
        """

        if not self.config.enabled:
            return CollectionResult(
                success=False,
                error=(
                    "Option-chain collector "
                    "is disabled."
                ),
                attempts=0,
            )

        params = self._build_params()

        return self._request(
            params=params
        )

    def collect_raw(self) -> Any:
        """
        Collect raw option-chain data.

        Raises:
            RuntimeError:
                When collection fails after all retries.
        """

        result = self.collect()

        if not result.success:
            raise RuntimeError(
                result.error
                or "Option-chain collection failed."
            )

        return result.data

    def collect_symbols(
        self,
        symbols: list[str],
    ) -> list[CollectionResult]:
        """
        Collect option-chain information for multiple symbols.

        Each symbol is collected independently.
        """

        results: list[CollectionResult] = []

        for symbol in symbols:
            results.append(
                self.collect_for_symbol(
                    symbol
                )
            )

        return results

    def collect_for_symbol(
        self,
        symbol: str,
    ) -> CollectionResult:
        """
        Collect option-chain data for one underlying symbol.
        """

        normalized_symbol = self._normalize_symbol(
            symbol
        )

        if not self.config.enabled:
            return CollectionResult(
                success=False,
                error=(
                    "Option-chain collector "
                    "is disabled."
                ),
                attempts=0,
            )

        params = self._build_params(
            symbol=normalized_symbol
        )

        return self._request(
            params=params
        )

    def close(self) -> None:
        """
        Close the underlying HTTP session.
        """

        self.session.close()

    def __enter__(
        self,
    ) -> "OptionChainCollector":
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        self.close()

    # ------------------------------------------------------------------
    # HTTP Request
    # ------------------------------------------------------------------

    def _request(
        self,
        *,
        params: Mapping[str, Any],
    ) -> CollectionResult:
        """
        Execute an HTTP GET request with retry handling.
        """

        url = self._build_url()

        attempts = 0
        last_error: Optional[str] = None
        last_status_code: Optional[int] = None

        for attempt in range(
            1,
            self.config.max_retries + 1,
        ):
            attempts = attempt

            try:
                response = self.session.get(
                    url,
                    params=dict(params),
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl,
                )

                last_status_code = (
                    response.status_code
                )

                if response.ok:
                    return CollectionResult(
                        success=True,
                        data=response.json(),
                        status_code=response.status_code,
                        attempts=attempt,
                    )

                last_error = (
                    "HTTP request failed: "
                    f"{response.status_code} "
                    f"{response.reason}"
                )

                if not self._is_retryable_status(
                    response.status_code
                ):
                    break

            except requests.Timeout as exc:
                last_error = (
                    "Option-chain request timed out: "
                    f"{exc}"
                )

            except requests.ConnectionError as exc:
                last_error = (
                    "Option-chain connection failed: "
                    f"{exc}"
                )

            except requests.RequestException as exc:
                last_error = (
                    "Option-chain request failed: "
                    f"{exc}"
                )

                break

            except ValueError as exc:
                last_error = (
                    "Invalid JSON response from "
                    f"option-chain endpoint: {exc}"
                )

                break

            if attempt < self.config.max_retries:
                self._sleep_before_retry(
                    attempt
                )

        return CollectionResult(
            success=False,
            data=None,
            status_code=last_status_code,
            error=last_error,
            attempts=attempts,
        )

    # ------------------------------------------------------------------
    # Request Construction
    # ------------------------------------------------------------------

    def _build_url(self) -> str:
        """
        Build the complete endpoint URL.
        """

        return (
            self.config.base_url.rstrip("/")
            + "/"
            + self.config.endpoint.lstrip("/")
        )

    def _build_params(
        self,
        *,
        symbol: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Build request query parameters.
        """

        requested_symbol = (
            symbol
            if symbol is not None
            else self.config.symbol
        )

        return {
            "underlying": self._normalize_symbol(
                requested_symbol
            )
        }

    # ------------------------------------------------------------------
    # Retry Handling
    # ------------------------------------------------------------------

    def _sleep_before_retry(
        self,
        attempt: int,
    ) -> None:
        """
        Sleep using exponential backoff.
        """

        delay = (
            self.config.retry_delay
            * (
                self.config.backoff_factor
                ** (attempt - 1)
            )
        )

        if delay > 0:
            time.sleep(delay)

    def _is_retryable_status(
        self,
        status_code: int,
    ) -> bool:
        """
        Determine whether an HTTP status should be retried.
        """

        return (
            status_code
            in self.RETRYABLE_STATUS_CODES
        )

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        """
        Normalize an option-chain underlying symbol.
        """

        if not isinstance(
            symbol,
            str,
        ):
            raise TypeError(
                "symbol must be a string."
            )

        normalized = (
            symbol.strip().upper()
        )

        if not normalized:
            raise ValueError(
                "symbol cannot be empty."
            )

        return normalized

    # ------------------------------------------------------------------
    # Configuration Validation
    # ------------------------------------------------------------------

    def _validate_config(
        self,
    ) -> None:
        """
        Validate collector configuration.
        """

        config = self.config

        if not isinstance(
            config.base_url,
            str,
        ):
            raise TypeError(
                "base_url must be a string."
            )

        if not config.base_url.strip():
            raise ValueError(
                "base_url cannot be empty."
            )

        if not isinstance(
            config.endpoint,
            str,
        ):
            raise TypeError(
                "endpoint must be a string."
            )

        if not config.endpoint.strip():
            raise ValueError(
                "endpoint cannot be empty."
            )

        self._normalize_symbol(
            config.symbol
        )

        if config.timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

        if config.max_retries < 1:
            raise ValueError(
                "max_retries must be at least 1."
            )

        if config.retry_delay < 0:
            raise ValueError(
                "retry_delay cannot be negative."
            )

        if config.backoff_factor < 1:
            raise ValueError(
                "backoff_factor must be at least 1."
            )

        if not isinstance(
            config.user_agent,
            str,
        ):
            raise TypeError(
                "user_agent must be a string."
            )