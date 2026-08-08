"""
Trades Collector

Collects raw trade data for the ETH futures data pipeline.

Responsibilities:
    - Fetch historical trades through REST
    - Receive live trades through WebSocket
    - Handle retries and request failures
    - Pass raw responses to the parser

This module does not:
    - Parse exchange responses
    - Validate records
    - Store data
    - Calculate features
    - Execute trades
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from ..base.rest_collector import RESTCollector
from ..base.websocket_collector import WebSocketCollector


class TradesCollector:
    """
    Runtime collector for ETH futures trade data.

    The collector is intentionally separated from parsing,
    validation, and storage.
    """

    collector_name = "trades"
    data_type = "trades"

    def __init__(
        self,
        rest_collector: Optional[RESTCollector] = None,
        websocket_collector: Optional[WebSocketCollector] = None,
        parser: Optional[Callable[[Any], Any]] = None,
        validator: Optional[Callable[[Any], Any]] = None,
        symbol: str = "ETHUSDT",
        market_type: str = "futures",
        max_retries: int = 5,
        retry_delay: float = 2.0,
    ) -> None:
        self.rest_collector = rest_collector
        self.websocket_collector = websocket_collector

        self.parser = parser
        self.validator = validator

        self.symbol = symbol.upper()
        self.market_type = market_type

        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # ==========================================================
    # Historical Trades
    # ==========================================================

    def collect_historical(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000,
    ) -> Any:
        """
        Collect historical trades.

        Parameters
        ----------
        start_time:
            Start timestamp in milliseconds.

        end_time:
            End timestamp in milliseconds.

        limit:
            Maximum number of records requested.

        Returns
        -------
        Any
            Raw exchange response.
        """

        if self.rest_collector is None:
            raise RuntimeError(
                "REST collector is not configured."
            )

        params: Dict[str, Any] = {
            "symbol": self.symbol,
            "limit": limit,
        }

        if start_time is not None:
            params["startTime"] = start_time

        if end_time is not None:
            params["endTime"] = end_time

        return self._request_with_retry(
            self.rest_collector,
            params,
        )

    # ==========================================================
    # Recent Trades
    # ==========================================================

    def collect_recent(
        self,
        limit: int = 1000,
    ) -> Any:
        """
        Collect the most recent trades.
        """

        if self.rest_collector is None:
            raise RuntimeError(
                "REST collector is not configured."
            )

        params = {
            "symbol": self.symbol,
            "limit": limit,
        }

        return self._request_with_retry(
            self.rest_collector,
            params,
        )

    # ==========================================================
    # Live Trades
    # ==========================================================

    def collect_live(
        self,
        callback: Callable[[Any], None],
    ) -> None:
        """
        Start live trade collection.

        Parsed/validated processing should be handled by
        downstream components through the callback.
        """

        if self.websocket_collector is None:
            raise RuntimeError(
                "WebSocket collector is not configured."
            )

        stream = self._build_trade_stream()

        self.websocket_collector.subscribe(
            stream=stream,
            callback=callback,
        )

    # ==========================================================
    # Stream Configuration
    # ==========================================================

    def _build_trade_stream(self) -> str:
        """
        Build the exchange trade WebSocket stream.

        The exact stream name is exchange-specific and should
        normally be supplied by the WebSocket collector.
        """

        symbol = self.symbol.lower()

        return f"{symbol}@trade"

    # ==========================================================
    # Retry Handling
    # ==========================================================

    def _request_with_retry(
        self,
        collector: RESTCollector,
        params: Dict[str, Any],
    ) -> Any:
        """
        Execute a REST request with retry handling.
        """

        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return collector.get(
                    params=params,
                )

            except Exception as exc:
                last_error = exc

                if attempt >= self.max_retries:
                    break

                delay = self.retry_delay * (2 ** (attempt - 1))

                time.sleep(delay)

        raise RuntimeError(
            f"Failed to collect trades for "
            f"{self.symbol} after "
            f"{self.max_retries} attempts."
        ) from last_error

    # ==========================================================
    # Parse
    # ==========================================================

    def parse(self, raw_data: Any) -> Any:
        """
        Parse raw exchange trade data.
        """

        if self.parser is None:
            raise RuntimeError(
                "Trade parser is not configured."
            )

        return self.parser(raw_data)

    # ==========================================================
    # Validate
    # ==========================================================

    def validate(self, parsed_data: Any) -> Any:
        """
        Validate parsed trade data.
        """

        if self.validator is None:
            raise RuntimeError(
                "Trade validator is not configured."
            )

        return self.validator(parsed_data)

    # ==========================================================
    # Collect → Parse → Validate
    # ==========================================================

    def collect_and_process(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000,
    ) -> Any:
        """
        Collect historical trades and pass them through
        parsing and validation.
        """

        raw_data = self.collect_historical(
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        parsed_data = self.parse(raw_data)

        validated_data = self.validate(parsed_data)

        return validated_data