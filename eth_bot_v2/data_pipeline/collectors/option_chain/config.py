"""
Option Chain Collector Configuration

Configuration for collecting ETH option-chain market data.

Responsibilities:
    - Store exchange/API configuration.
    - Store request timeout settings.
    - Store retry and backoff settings.
    - Store symbol configuration.
    - Store HTTP/session settings.
    - Validate configuration values.

This module does not:
    - Make API requests.
    - Parse API responses.
    - Validate option-chain records.
    - Calculate Greeks.
    - Calculate implied volatility.
    - Generate features.
    - Generate trading signals.
    - Perform risk management.
    - Execute trades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


@dataclass(frozen=True, slots=True)
class OptionChainConfig:
    """
    Configuration for the ETH option-chain collector.
    """

    # ------------------------------------------------------------------
    # Exchange
    # ------------------------------------------------------------------

    base_url: str = "https://eapi.binance.com"

    endpoint: str = "/eapi/v1/exchangeInfo"

    # ------------------------------------------------------------------
    # Instrument
    # ------------------------------------------------------------------

    underlying_symbol: str = "ETH"

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    timeout: float = 10.0

    verify_ssl: bool = True

    user_agent: str = (
        "eth-bot-option-chain-collector/1.0"
    )

    # ------------------------------------------------------------------
    # Retry
    # ------------------------------------------------------------------

    max_retries: int = 3

    retry_delay: float = 1.0

    backoff_factor: float = 2.0

    retryable_status_codes: FrozenSet[int] = field(
        default_factory=lambda: frozenset(
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
    )

    # ------------------------------------------------------------------
    # Collector
    # ------------------------------------------------------------------

    enabled: bool = True

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        """
        Validate configuration immediately after creation.
        """

        self._validate_base_url()
        self._validate_endpoint()
        self._validate_symbol()
        self._validate_timeout()
        self._validate_retries()
        self._validate_retry_delay()
        self._validate_backoff_factor()
        self._validate_retryable_status_codes()
        self._validate_user_agent()
        self._validate_boolean_options()

    # ------------------------------------------------------------------
    # Base URL
    # ------------------------------------------------------------------

    def _validate_base_url(self) -> None:
        """
        Validate the exchange base URL.
        """

        if not isinstance(
            self.base_url,
            str,
        ):
            raise TypeError(
                "base_url must be a string."
            )

        if not self.base_url.strip():
            raise ValueError(
                "base_url cannot be empty."
            )

        normalized = self.base_url.strip()

        if not (
            normalized.startswith(
                "https://"
            )
            or normalized.startswith(
                "http://"
            )
        ):
            raise ValueError(
                "base_url must start with "
                "'https://' or 'http://'."
            )

    # ------------------------------------------------------------------
    # Endpoint
    # ------------------------------------------------------------------

    def _validate_endpoint(self) -> None:
        """
        Validate the exchange API endpoint.
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

    # ------------------------------------------------------------------
    # Symbol
    # ------------------------------------------------------------------

    def _validate_symbol(self) -> None:
        """
        Validate the underlying option-chain symbol.
        """

        if not isinstance(
            self.underlying_symbol,
            str,
        ):
            raise TypeError(
                "underlying_symbol must be a string."
            )

        if not self.underlying_symbol.strip():
            raise ValueError(
                "underlying_symbol cannot be empty."
            )

        if (
            self.underlying_symbol.strip()
            != self.underlying_symbol
        ):
            raise ValueError(
                "underlying_symbol cannot contain "
                "leading or trailing whitespace."
            )

        if (
            self.underlying_symbol
            != self.underlying_symbol.upper()
        ):
            raise ValueError(
                "underlying_symbol must be uppercase."
            )

    # ------------------------------------------------------------------
    # Timeout
    # ------------------------------------------------------------------

    def _validate_timeout(self) -> None:
        """
        Validate HTTP timeout.
        """

        if isinstance(
            self.timeout,
            bool,
        ):
            raise TypeError(
                "timeout must be a number, "
                "not a boolean."
            )

        if not isinstance(
            self.timeout,
            (int, float),
        ):
            raise TypeError(
                "timeout must be an int or float."
            )

        if self.timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

    # ------------------------------------------------------------------
    # Retries
    # ------------------------------------------------------------------

    def _validate_retries(self) -> None:
        """
        Validate retry count.
        """

        if isinstance(
            self.max_retries,
            bool,
        ):
            raise TypeError(
                "max_retries must be an integer, "
                "not a boolean."
            )

        if not isinstance(
            self.max_retries,
            int,
        ):
            raise TypeError(
                "max_retries must be an integer."
            )

        if self.max_retries < 1:
            raise ValueError(
                "max_retries must be at least 1."
            )

    # ------------------------------------------------------------------
    # Retry Delay
    # ------------------------------------------------------------------

    def _validate_retry_delay(self) -> None:
        """
        Validate initial retry delay.
        """

        if isinstance(
            self.retry_delay,
            bool,
        ):
            raise TypeError(
                "retry_delay must be a number, "
                "not a boolean."
            )

        if not isinstance(
            self.retry_delay,
            (int, float),
        ):
            raise TypeError(
                "retry_delay must be an int or float."
            )

        if self.retry_delay < 0:
            raise ValueError(
                "retry_delay cannot be negative."
            )

    # ------------------------------------------------------------------
    # Backoff
    # ------------------------------------------------------------------

    def _validate_backoff_factor(self) -> None:
        """
        Validate exponential backoff factor.
        """

        if isinstance(
            self.backoff_factor,
            bool,
        ):
            raise TypeError(
                "backoff_factor must be a number, "
                "not a boolean."
            )

        if not isinstance(
            self.backoff_factor,
            (int, float),
        ):
            raise TypeError(
                "backoff_factor must be an int "
                "or float."
            )

        if self.backoff_factor < 1:
            raise ValueError(
                "backoff_factor must be at least 1."
            )

    # ------------------------------------------------------------------
    # Retryable Status Codes
    # ------------------------------------------------------------------

    def _validate_retryable_status_codes(
        self,
    ) -> None:
        """
        Validate retryable HTTP status codes.
        """

        if not isinstance(
            self.retryable_status_codes,
            frozenset,
        ):
            raise TypeError(
                "retryable_status_codes must be "
                "a frozenset."
            )

        for status_code in (
            self.retryable_status_codes
        ):
            if isinstance(
                status_code,
                bool,
            ):
                raise TypeError(
                    "HTTP status codes must be "
                    "integers."
                )

            if not isinstance(
                status_code,
                int,
            ):
                raise TypeError(
                    "HTTP status codes must be "
                    "integers."
                )

            if not (
                100
                <= status_code
                <= 599
            ):
                raise ValueError(
                    "HTTP status codes must be "
                    "between 100 and 599."
                )

    # ------------------------------------------------------------------
    # User Agent
    # ------------------------------------------------------------------

    def _validate_user_agent(self) -> None:
        """
        Validate HTTP User-Agent.
        """

        if not isinstance(
            self.user_agent,
            str,
        ):
            raise TypeError(
                "user_agent must be a string."
            )

        if not self.user_agent.strip():
            raise ValueError(
                "user_agent cannot be empty."
            )

    # ------------------------------------------------------------------
    # Boolean Options
    # ------------------------------------------------------------------

    def _validate_boolean_options(self) -> None:
        """
        Validate boolean configuration flags.
        """

        if not isinstance(
            self.verify_ssl,
            bool,
        ):
            raise TypeError(
                "verify_ssl must be a boolean."
            )

        if not isinstance(
            self.enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be a boolean."
            )


# ----------------------------------------------------------------------
# Default Configuration
# ----------------------------------------------------------------------

DEFAULT_OPTION_CHAIN_CONFIG = (
    OptionChainConfig()
)


# ----------------------------------------------------------------------
# Factory
# ----------------------------------------------------------------------

def get_option_chain_config() -> OptionChainConfig:
    """
    Return the default option-chain configuration.
    """

    return DEFAULT_OPTION_CHAIN_CONFIG