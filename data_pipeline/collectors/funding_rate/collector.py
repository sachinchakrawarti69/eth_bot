
"""
Funding Rate Collector

Collects perpetual futures funding-rate data from an exchange.

Responsibilities:
    - Fetch historical funding-rate records through REST.
    - Fetch the latest funding-rate record when required.
    - Handle pagination for historical data.
    - Delegate retries to the base collector layer.
    - Return raw exchange responses to the parser.

This module does not:
    - Parse exchange-specific payloads.
    - Validate funding-rate values.
    - Calculate funding-rate features.
    - Store data.
    - Make trading decisions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from ..base.base_collector import BaseCollector


class FundingRateCollector(BaseCollector):
    """
    Collector for perpetual futures funding-rate data.

    The collector is intentionally exchange-facing only.
    Exchange-specific endpoint details should be supplied through
    configuration rather than embedded throughout the pipeline.
    """

    collector_name = "funding_rate"
    collector_version = "1.0"

    def __init__(
        self,
        client: Any,
        config: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """
        Initialize the funding-rate collector.

        Parameters
        ----------
        client:
            Exchange REST/API client.

        config:
            Collector configuration.
        """

        super().__init__()

        self.client = client
        self.config = dict(config or {})

        self.symbol = self.config.get(
            "symbol",
            "ETHUSDT",
        )

        self.limit = int(
            self.config.get(
                "limit",
                1000,
            )
        )

        self.max_pages = int(
            self.config.get(
                "max_pages",
                100,
            )
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def collect(
        self,
        *,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Collect funding-rate history.

        Parameters
        ----------
        symbol:
            Futures symbol. Defaults to configured symbol.

        start_time:
            Start timestamp in milliseconds.

        end_time:
            End timestamp in milliseconds.

        limit:
            Maximum records requested per API call.

        Returns
        -------
        list[dict]
            Raw exchange funding-rate records.
        """

        symbol = symbol or self.symbol
        limit = limit or self.limit

        self._validate_request(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return self._collect_paginated(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    def collect_latest(
        self,
        *,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Collect the most recent funding-rate record.

        Returns the raw exchange response without parsing it.
        """

        symbol = symbol or self.symbol

        self._validate_symbol(symbol)

        response = self._request(
            symbol=symbol,
            limit=1,
        )

        return self._normalize_response(response)

    def collect_range(
        self,
        start_time: int,
        end_time: int,
        *,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Collect funding-rate records for a specific time range.
        """

        return self.collect(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
        )

    # ==========================================================
    # Pagination
    # ==========================================================

    def _collect_paginated(
        self,
        *,
        symbol: str,
        start_time: Optional[int],
        end_time: Optional[int],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Collect all records across paginated API responses.

        Pagination is based on the timestamp of the last returned
        record rather than assuming a fixed funding interval.
        """

        records: List[Dict[str, Any]] = []

        current_start = start_time

        for _ in range(self.max_pages):
            response = self._request(
                symbol=symbol,
                start_time=current_start,
                end_time=end_time,
                limit=limit,
            )

            page = self._normalize_response(
                response
            )

            if not page:
                break

            records.extend(page)

            if len(page) < limit:
                break

            next_start = self._extract_last_timestamp(
                page
            )

            if next_start is None:
                break

            # Prevent infinite pagination if the exchange
            # repeatedly returns the same page.
            if (
                current_start is not None
                and next_start <= current_start
            ):
                break

            current_start = next_start + 1

            if (
                end_time is not None
                and current_start >= end_time
            ):
                break

        return self._deduplicate_records(
            records
        )

    # ==========================================================
    # API Request
    # ==========================================================

    def _request(
        self,
        *,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Any:
        """
        Execute one exchange funding-rate request.

        The concrete client interface can be adapted here or
        supplied through an exchange-specific client adapter.
        """

        params: Dict[str, Any] = {
            "symbol": symbol,
        }

        if start_time is not None:
            params["startTime"] = start_time

        if end_time is not None:
            params["endTime"] = end_time

        if limit is not None:
            params["limit"] = limit

        request_method = getattr(
            self.client,
            "get_funding_rate_history",
            None,
        )

        if request_method is None:
            raise AttributeError(
                "Exchange client must provide "
                "'get_funding_rate_history'."
            )

        return self._execute_with_retry(
            request_method,
            params,
        )

    # ==========================================================
    # Retry Boundary
    # ==========================================================

    def _execute_with_retry(
        self,
        request_method: Any,
        params: Mapping[str, Any],
    ) -> Any:
        """
        Execute an API request.

        If the base collector provides a retry mechanism,
        use it. Otherwise execute the request directly.
        """

        retry_method = getattr(
            self,
            "retry",
            None,
        )

        if callable(retry_method):
            return retry_method(
                request_method,
                **dict(params),
            )

        return request_method(
            **dict(params)
        )

    # ==========================================================
    # Response Normalization
    # ==========================================================

    @staticmethod
    def _normalize_response(
        response: Any,
    ) -> List[Dict[str, Any]]:
        """
        Normalize the outer API response into a list.

        This does NOT parse individual funding-rate fields.
        That remains the parser's responsibility.
        """

        if response is None:
            return []

        if isinstance(response, list):
            return [
                item
                for item in response
                if isinstance(item, Mapping)
            ]

        if isinstance(response, Mapping):
            # Some exchange clients wrap the actual records.
            for key in (
                "data",
                "result",
                "rows",
            ):
                value = response.get(key)

                if isinstance(value, list):
                    return [
                        item
                        for item in value
                        if isinstance(
                            item,
                            Mapping,
                        )
                    ]

            return [dict(response)]

        raise TypeError(
            "Unsupported funding-rate API response: "
            f"{type(response).__name__}"
        )

    # ==========================================================
    # Timestamp Handling
    # ==========================================================

    @staticmethod
    def _extract_last_timestamp(
        records: List[Mapping[str, Any]],
    ) -> Optional[int]:
        """
        Extract the latest funding timestamp from a page.

        Supports common exchange field names.
        """

        if not records:
            return None

        last = records[-1]

        for key in (
            "fundingTime",
            "funding_time",
            "timestamp",
            "time",
        ):
            value = last.get(key)

            if value is not None:
                try:
                    return int(value)
                except (
                    TypeError,
                    ValueError,
                ):
                    return None

        return None

    # ==========================================================
    # Deduplication
    # ==========================================================

    @staticmethod
    def _deduplicate_records(
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate records while preserving order.
        """

        if not records:
            return []

        seen = set()
        result: List[Dict[str, Any]] = []

        for record in records:
            key = (
                record.get("symbol"),
                record.get("fundingTime"),
                record.get("funding_time"),
                record.get("timestamp"),
                record.get("time"),
            )

            # If no timestamp exists, retain the record rather
            # than accidentally dropping unrelated records.
            if all(value is None for value in key):
                result.append(record)
                continue

            if key in seen:
                continue

            seen.add(key)
            result.append(record)

        return result

    # ==========================================================
    # Request Validation
    # ==========================================================

    def _validate_request(
        self,
        *,
        symbol: str,
        start_time: Optional[int],
        end_time: Optional[int],
        limit: int,
    ) -> None:
        """
        Validate collection parameters.
        """

        self._validate_symbol(symbol)

        if limit <= 0:
            raise ValueError(
                "Funding-rate limit must be greater than zero."
            )

        if limit > 1000:
            raise ValueError(
                "Funding-rate limit exceeds the configured "
                "maximum of 1000."
            )

        if start_time is not None:
            self._validate_timestamp(
                start_time,
                "start_time",
            )

        if end_time is not None:
            self._validate_timestamp(
                end_time,
                "end_time",
            )

        if (
            start_time is not None
            and end_time is not None
            and start_time >= end_time
        ):
            raise ValueError(
                "start_time must be earlier than end_time."
            )

    @staticmethod
    def _validate_symbol(
        symbol: str,
    ) -> None:
        if not isinstance(symbol, str):
            raise TypeError(
                "Funding-rate symbol must be a string."
            )

        if not symbol.strip():
            raise ValueError(
                "Funding-rate symbol cannot be empty."
            )

    @staticmethod
    def _validate_timestamp(
        value: int,
        field_name: str,
    ) -> None:
        if not isinstance(value, int):
            raise TypeError(
                f"{field_name} must be an integer "
                "Unix timestamp in milliseconds."
            )

        if value < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )


