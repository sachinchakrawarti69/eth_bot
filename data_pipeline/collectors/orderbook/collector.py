"""
Order Book Collector

Collects order-book market data for the ETH futures data pipeline.

Responsibilities:
    - Collect historical/current order-book snapshots through REST
    - Collect live order-book updates through WebSocket
    - Handle retry and reconnect behavior
    - Pass raw responses to the parser

This module does not:
    - Parse exchange responses
    - Validate order-book records
    - Store data
    - Calculate order-book features
    - Generate ML features
    - Execute trades
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from ..base.rest_collector import RESTCollector
from ..base.websocket_collector import WebSocketCollector


class OrderBookCollector:
    """
    Runtime collector for ETH futures order-book data.

    Supports:
        - REST snapshots
        - Live WebSocket depth updates
        - Retry handling
        - Parser/validator integration
    """

    collector_name = "orderbook"
    data_type = "orderbook"

    def __init__(
        self,
        rest_collector: Optional[RESTCollector] = None,
        websocket_collector: Optional[WebSocketCollector] = None,
        parser: Optional[Callable[[Any], Any]] = None,
        validator: Optional[Callable[[Any], Any]] = None,
        symbol: str = "ETHUSDT",
        market_type: str = "futures",
        depth_limit: int = 100,
        max_retries: int = 5,
        retry_delay: float = 2.0,
    ) -> None:
        self.rest_collector = rest_collector
        self.websocket_collector = websocket_collector

        self.parser = parser
        self.validator = validator

        self.symbol = symbol.upper()
        self.market_type = market_type

        self.depth_limit = depth_limit

        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # ==========================================================
    # REST Snapshot
    # ==========================================================

    def collect_snapshot(
        self,
        limit: Optional[int] = None,
    ) -> Any:
        """
        Collect the current order-book snapshot.

        Parameters
        ----------
        limit:
            Number of order-book levels requested.

        Returns
        -------
        Any
            Raw exchange response.
        """

        if self.rest_collector is None:
            raise RuntimeError(
                "REST collector is not configured."
            )

        depth_limit = (
            limit
            if limit is not None
            else self.depth_limit
        )

        params: Dict[str, Any] = {
            "symbol": self.symbol,
            "limit": depth_limit,
        }

        return self._request_with_retry(
            self.rest_collector,
            params,
        )

    # ==========================================================
    # Live Order Book
    # ==========================================================

    def collect_live(
        self,
        callback: Callable[[Any], None],
    ) -> None:
        """
        Start live order-book collection.

        The callback receives raw WebSocket events.

        Parsing and validation should be performed
        downstream.
        """

        if self.websocket_collector is None:
            raise RuntimeError(
                "WebSocket collector is not configured."
            )

        stream = self._build_depth_stream()

        self.websocket_collector.subscribe(
            stream=stream,
            callback=callback,
        )

    # ==========================================================
    # Stream
    # ==========================================================

    def _build_depth_stream(self) -> str:
        """
        Build the exchange depth stream identifier.

        The exact stream name is exchange-specific and should
        eventually be handled by the exchange transport layer.
        """

        symbol = self.symbol.lower()

        return f"{symbol}@depth"

    # ==========================================================
    # Retry
    # ==========================================================

    def _request_with_retry(
        self,
        collector: RESTCollector,
        params: Dict[str, Any],
    ) -> Any:
        """
        Execute a REST request with exponential backoff.
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

                delay = self.retry_delay * (
                    2 ** (attempt - 1)
                )

                time.sleep(delay)

        raise RuntimeError(
            f"Failed to collect order book for "
            f"{self.symbol} after "
            f"{self.max_retries} attempts."
        ) from last_error

    # ==========================================================
    # Parse
    # ==========================================================

    def parse(
        self,
        raw_data: Any,
    ) -> Any:
        """
        Parse raw order-book data.
        """

        if self.parser is None:
            raise RuntimeError(
                "Order-book parser is not configured."
            )

        return self.parser(raw_data)

    # ==========================================================
    # Validate
    # ==========================================================

    def validate(
        self,
        parsed_data: Any,
    ) -> Any:
        """
        Validate parsed order-book data.
        """

        if self.validator is None:
            raise RuntimeError(
                "Order-book validator is not configured."
            )

        return self.validator(parsed_data)

    # ==========================================================
    # Snapshot Processing
    # ==========================================================

    def collect_and_process(
        self,
        limit: Optional[int] = None,
    ) -> Any:
        """
        Collect a snapshot and process it through:

            Collect → Parse → Validate
        """

        raw_data = self.collect_snapshot(
            limit=limit,
        )

        parsed_data = self.parse(raw_data)

        return self.validate(parsed_data)