"""
Open Interest Collector

Collects open-interest data for ETH perpetual futures from an
exchange REST API.

Responsibilities:
    - Build open-interest API requests.
    - Collect latest open-interest data.
    - Collect historical open-interest data.
    - Handle pagination.
    - Delegate retries to the shared retry layer.
    - Return raw exchange responses.

This module does not:
    - Parse exchange responses.
    - Validate normalized records.
    - Store data.
    - Calculate open-interest features.
    - Generate trading signals.
    - Make trading decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from ..base.rest_collector import RestCollector


class OpenInterestCollector(RestCollector):
    """
    Collector for open-interest data.

    The collector intentionally returns raw exchange records.
    Parsing and validation are handled by separate modules.
    """

    collector_name = "open_interest"
    collector_version = "1.0"

    DEFAULT_ENDPOINT = "/futures/data/openInterestHist"

    DEFAULT_SYMBOL = "ETHUSDT"
    DEFAULT_PERIOD = "1h"

    DEFAULT_LIMIT = 500
    MAX_LIMIT = 500

    DEFAULT_MAX_PAGES = 100

    def __init__(
        self,
        config: Optional[Any] = None,
        client: Optional[Any] = None,
    ) -> None:
        """
        Initialize the open-interest collector.

        Parameters
        ----------
        config:
            Open-interest collector configuration.

        client:
            REST client used to communicate with the exchange.
        """

        super().__init__(
            config=config,
            client=client,
        )

        self.symbol = self._get_config_value(
            "symbol",
            self.DEFAULT_SYMBOL,
        )

        self.period = self._get_config_value(
            "period",
            self.DEFAULT_PERIOD,
        )

        self.limit = int(
            self._get_config_value(
                "limit",
                self.DEFAULT_LIMIT,
            )
        )

        self.max_pages = int(
            self._get_config_value(
                "max_pages",
                self.DEFAULT_MAX_PAGES,
            )
        )

        self.endpoint = self._get_config_value(
            "endpoint",
            self.DEFAULT_ENDPOINT,
        )

        self._validate_configuration()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect_latest(
        self,
        *,
        symbol: Optional[str] = None,
        period: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Collect the latest open-interest records.

        Returns
        -------
        list[dict]
            Raw exchange records.
        """

        request_params = self._build_params(
            symbol=symbol,
            period=period,
            limit=limit,
        )

        response = self._request(
            request_params
        )

        return self._extract_records(
            response
        )

    def collect_historical(
        self,
        *,
        start_time: int | datetime,
        end_time: Optional[int | datetime] = None,
        symbol: Optional[str] = None,
        period: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Collect historical open-interest records.

        Pagination continues until:
            - the requested end time is reached,
            - the exchange returns no records,
            - no forward progress is possible,
            - max_pages is reached.

        Returns
        -------
        list[dict]
            Raw exchange records.
        """

        start_ms = self._normalize_timestamp(
            start_time
        )

        end_ms = (
            self._normalize_timestamp(end_time)
            if end_time is not None
            else None
        )

        if (
            end_ms is not None
            and start_ms >= end_ms
        ):
            raise ValueError(
                "start_time must be earlier than end_time."
            )

        request_limit = self._normalize_limit(
            limit
        )

        request_symbol = (
            symbol or self.symbol
        )

        request_period = (
            period or self.period
        )

        records: List[Dict[str, Any]] = []

        current_start = start_ms

        for _ in range(self.max_pages):
            params = self._build_params(
                symbol=request_symbol,
                period=request_period,
                limit=request_limit,
                start_time=current_start,
                end_time=end_ms,
            )

            response = self._request(
                params
            )

            page = self._extract_records(
                response
            )

            if not page:
                break

            records.extend(page)

            next_start = (
                self._get_next_start_time(
                    page
                )
            )

            if next_start is None:
                break

            if (
                end_ms is not None
                and next_start >= end_ms
            ):
                break

            if next_start <= current_start:
                break

            current_start = next_start

            if (
                end_ms is not None
                and current_start >= end_ms
            ):
                break

        return self._deduplicate_records(
            records
        )

    def collect(
        self,
        *,
        start_time: Optional[int | datetime] = None,
        end_time: Optional[int | datetime] = None,
        symbol: Optional[str] = None,
        period: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Unified collection interface.

        If start_time is supplied, historical collection is used.
        Otherwise, the latest records are collected.
        """

        if start_time is not None:
            return self.collect_historical(
                start_time=start_time,
                end_time=end_time,
                symbol=symbol,
                period=period,
                limit=limit,
            )

        return self.collect_latest(
            symbol=symbol,
            period=period,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Request construction
    # ------------------------------------------------------------------

    def _build_params(
        self,
        *,
        symbol: Optional[str] = None,
        period: Optional[str] = None,
        limit: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Build exchange API parameters.
        """

        request_symbol = (
            symbol or self.symbol
        )

        request_period = (
            period or self.period
        )

        request_limit = self._normalize_limit(
            limit
        )

        params: Dict[str, Any] = {
            "symbol": request_symbol,
            "period": request_period,
            "limit": request_limit,
        }

        if start_time is not None:
            params["startTime"] = start_time

        if end_time is not None:
            params["endTime"] = end_time

        return params

    # ------------------------------------------------------------------
    # REST request
    # ------------------------------------------------------------------

    def _request(
        self,
        params: Mapping[str, Any],
    ) -> Any:
        """
        Execute the REST request through the configured client.

        The base REST collector is responsible for network-level
        behavior such as authentication, timeout handling and
        retry integration.
        """

        if self.client is None:
            raise RuntimeError(
                "REST client is not configured."
            )

        if hasattr(self, "request"):
            return self.request(
                method="GET",
                endpoint=self.endpoint,
                params=dict(params),
            )

        if hasattr(
            self.client,
            "get",
        ):
            return self.client.get(
                self.endpoint,
                params=dict(params),
            )

        raise RuntimeError(
            "Configured REST client does not provide "
            "a supported GET interface."
        )

    # ------------------------------------------------------------------
    # Response handling
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_records(
        response: Any,
    ) -> List[Dict[str, Any]]:
        """
        Extract raw records from common exchange response formats.
        """

        if response is None:
            return []

        if isinstance(response, list):
            return [
                dict(record)
                for record in response
                if isinstance(record, Mapping)
            ]

        if isinstance(response, Mapping):
            for key in (
                "data",
                "result",
                "rows",
                "list",
            ):
                value = response.get(key)

                if isinstance(value, list):
                    return [
                        dict(record)
                        for record in value
                        if isinstance(
                            record,
                            Mapping,
                        )
                    ]

            return [dict(response)]

        raise TypeError(
            "Unsupported open-interest response type: "
            f"{type(response).__name__}"
        )

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    @staticmethod
    def _get_next_start_time(
        records: List[Mapping[str, Any]],
    ) -> Optional[int]:
        """
        Determine the next historical pagination timestamp.

        Supports common exchange timestamp field names.
        """

        timestamps: List[int] = []

        timestamp_fields = (
            "timestamp",
            "time",
            "T",
            "openTime",
            "open_time",
        )

        for record in records:
            for field in timestamp_fields:
                if field not in record:
                    continue

                value = record[field]

                try:
                    timestamp = int(
                        float(value)
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                if timestamp < 100_000_000_000:
                    timestamp *= 1000

                timestamps.append(
                    timestamp
                )
                break

        if not timestamps:
            return None

        return max(timestamps) + 1

    @staticmethod
    def _deduplicate_records(
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate records using symbol + timestamp.
        """

        seen = set()
        result: List[Dict[str, Any]] = []

        for record in records:
            symbol = (
                record.get("symbol")
                or record.get("s")
            )

            timestamp = (
                record.get("timestamp")
                or record.get("time")
                or record.get("T")
                or record.get("openTime")
                or record.get("open_time")
            )

            if timestamp is not None:
                try:
                    timestamp = int(
                        float(timestamp)
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    timestamp = None

            key = (
                symbol,
                timestamp,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(record)

        return result

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def _validate_configuration(
        self,
    ) -> None:
        """
        Validate collector configuration.
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

        if self.limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if self.limit > self.MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed {self.MAX_LIMIT}."
            )

        if self.max_pages <= 0:
            raise ValueError(
                "max_pages must be greater than zero."
            )

    def _normalize_limit(
        self,
        limit: Optional[int],
    ) -> int:
        """
        Normalize and validate request limit.
        """

        value = (
            self.limit
            if limit is None
            else int(limit)
        )

        if value <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if value > self.MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed {self.MAX_LIMIT}."
            )

        return value

    def _get_config_value(
        self,
        name: str,
        default: Any,
    ) -> Any:
        """
        Read a configuration value from either an object
        or mapping.
        """

        if self.config is None:
            return default

        if isinstance(
            self.config,
            Mapping,
        ):
            return self.config.get(
                name,
                default,
            )

        return getattr(
            self.config,
            name,
            default,
        )

    # ------------------------------------------------------------------
    # Timestamp helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_timestamp(
        value: int | datetime,
    ) -> int:
        """
        Normalize timestamp to Unix milliseconds.
        """

        if isinstance(
            value,
            datetime,
        ):
            if value.tzinfo is None:
                value = value.replace(
                    tzinfo=timezone.utc
                )

            return int(
                value.timestamp() * 1000
            )

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                "Timestamp cannot be boolean."
            )

        timestamp = int(value)

        if timestamp < 0:
            raise ValueError(
                "Timestamp cannot be negative."
            )

        if timestamp < 100_000_000_000:
            timestamp *= 1000

        return timestamp