"""
Liquidations Collector

Collects ETH futures liquidation data from an exchange REST API.

Responsibilities:
    - Build liquidation-data requests.
    - Request historical liquidation data.
    - Support pagination.
    - Handle request retries through the configured client.
    - Normalize collection boundaries.
    - Return raw exchange records to the parser.

This module does not:
    - Parse exchange-specific response fields.
    - Validate liquidation records.
    - Calculate liquidation features.
    - Generate trading signals.
    - Manage risk.
    - Execute trades.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence


class RestClientProtocol(Protocol):
    """
    Minimal REST client interface required by the collector.
    """

    def get(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any],
        timeout: Optional[float] = None,
    ) -> Any:
        ...


class LiquidationCollector:
    """
    Collector for ETH futures liquidation data.

    The collector is intentionally exchange-client agnostic.
    The injected REST client is responsible for HTTP transport,
    authentication, rate limiting, and low-level retry behavior.
    """

    collector_name = "liquidations"
    collector_version = "1.0"

    def __init__(
        self,
        client: RestClientProtocol,
        config: Any,
    ) -> None:
        """
        Initialize the liquidation collector.

        Parameters
        ----------
        client:
            REST client implementing the required get() interface.

        config:
            Liquidation collector configuration.
        """

        if client is None:
            raise ValueError(
                "client cannot be None."
            )

        if config is None:
            raise ValueError(
                "config cannot be None."
            )

        self.client = client
        self.config = config

    # ------------------------------------------------------------------
    # Public collection API
    # ------------------------------------------------------------------

    def collect(
        self,
        *,
        start_time: Optional[int | datetime] = None,
        end_time: Optional[int | datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Mapping[str, Any]]:
        """
        Collect liquidation records.

        Parameters
        ----------
        start_time:
            Optional inclusive start timestamp.

        end_time:
            Optional inclusive end timestamp.

        limit:
            Optional records-per-request override.

        Returns
        -------
        list[Mapping]
            Raw exchange liquidation records.
        """

        start_ms = self._normalize_timestamp(
            start_time
        )

        end_ms = self._normalize_timestamp(
            end_time
        )

        self._validate_time_range(
            start_ms,
            end_ms,
        )

        request_limit = self._resolve_limit(
            limit
        )

        params = self._build_params(
            start_time=start_ms,
            end_time=end_ms,
            limit=request_limit,
        )

        response = self._request(
            params=params
        )

        return self._extract_records(
            response
        )

    def collect_latest(
        self,
        *,
        limit: Optional[int] = None,
    ) -> List[Mapping[str, Any]]:
        """
        Collect the latest liquidation records.
        """

        request_limit = self._resolve_limit(
            limit
        )

        response = self._request(
            params=self._build_params(
                limit=request_limit
            )
        )

        return self._extract_records(
            response
        )

    def collect_historical(
        self,
        *,
        start_time: int | datetime,
        end_time: int | datetime,
        limit: Optional[int] = None,
    ) -> List[Mapping[str, Any]]:
        """
        Collect historical liquidation records using pagination.

        Pagination continues until:
            - No records are returned.
            - The requested end time is reached.
            - The configured maximum page count is reached.
            - The API stops returning new records.
        """

        start_ms = self._normalize_timestamp(
            start_time
        )

        end_ms = self._normalize_timestamp(
            end_time
        )

        self._validate_time_range(
            start_ms,
            end_ms,
        )

        request_limit = self._resolve_limit(
            limit
        )

        all_records: List[Mapping[str, Any]] = []

        current_start = start_ms
        previous_last_timestamp: Optional[int] = None

        max_pages = int(
            getattr(
                self.config,
                "max_pages",
                100,
            )
        )

        for _ in range(max_pages):
            params = self._build_params(
                start_time=current_start,
                end_time=end_ms,
                limit=request_limit,
            )

            response = self._request(
                params=params
            )

            records = self._extract_records(
                response
            )

            if not records:
                break

            all_records.extend(records)

            last_timestamp = self._find_last_timestamp(
                records
            )

            if last_timestamp is None:
                break

            if (
                previous_last_timestamp is not None
                and last_timestamp <= previous_last_timestamp
            ):
                break

            previous_last_timestamp = last_timestamp

            if last_timestamp >= end_ms:
                break

            current_start = last_timestamp + 1

        return self._deduplicate_records(
            all_records
        )

    # ------------------------------------------------------------------
    # Request construction
    # ------------------------------------------------------------------

    def _build_params(
        self,
        *,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Build exchange API request parameters.
        """

        symbol = getattr(
            self.config,
            "symbol",
            "ETHUSDT",
        )

        params: Dict[str, Any] = {
            "symbol": symbol,
        }

        if limit is not None:
            params["limit"] = limit

        if start_time is not None:
            params["startTime"] = start_time

        if end_time is not None:
            params["endTime"] = end_time

        return params

    # ------------------------------------------------------------------
    # HTTP request
    # ------------------------------------------------------------------

    def _request(
        self,
        *,
        params: Mapping[str, Any],
    ) -> Any:
        """
        Execute a REST request through the injected client.
        """

        endpoint = getattr(
            self.config,
            "endpoint",
            "/futures/data/allForceOrders",
        )

        timeout = getattr(
            self.config,
            "request_timeout",
            10.0,
        )

        response = self.client.get(
            endpoint,
            params=params,
            timeout=timeout,
        )

        return response

    # ------------------------------------------------------------------
    # Response extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_records(
        response: Any,
    ) -> List[Mapping[str, Any]]:
        """
        Extract raw liquidation records from common API response
        structures.

        Parsing and field normalization remain the responsibility
        of parser.py.
        """

        if response is None:
            return []

        if isinstance(response, list):
            return [
                record
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
                        record
                        for record in value
                        if isinstance(record, Mapping)
                    ]

            return [response]

        raise TypeError(
            "Unsupported liquidation response type: "
            f"{type(response).__name__}"
        )

    # ------------------------------------------------------------------
    # Limit handling
    # ------------------------------------------------------------------

    def _resolve_limit(
        self,
        limit: Optional[int],
    ) -> int:
        """
        Resolve and validate the request limit.
        """

        if limit is None:
            limit = int(
                getattr(
                    self.config,
                    "limit",
                    100,
                )
            )

        max_limit = int(
            getattr(
                self.config,
                "max_limit",
                limit,
            )
        )

        if isinstance(limit, bool):
            raise TypeError(
                "limit must be an integer."
            )

        if not isinstance(limit, int):
            raise TypeError(
                "limit must be an integer."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if limit > max_limit:
            raise ValueError(
                "limit cannot exceed max_limit."
            )

        return limit

    # ------------------------------------------------------------------
    # Timestamp utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_timestamp(
        value: Optional[int | datetime],
    ) -> Optional[int]:
        """
        Normalize timestamps to Unix milliseconds.
        """

        if value is None:
            return None

        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(
                    tzinfo=timezone.utc
                )

            return int(
                value.timestamp() * 1000
            )

        if isinstance(value, bool):
            raise TypeError(
                "timestamp must be an integer or datetime."
            )

        if not isinstance(value, int):
            raise TypeError(
                "timestamp must be an integer or datetime."
            )

        if value < 0:
            raise ValueError(
                "timestamp cannot be negative."
            )

        # Treat small timestamps as seconds.
        if value < 100_000_000_000:
            return value * 1000

        return value

    @staticmethod
    def _validate_time_range(
        start_time: Optional[int],
        end_time: Optional[int],
    ) -> None:
        """
        Validate collection time boundaries.
        """

        if (
            start_time is not None
            and end_time is not None
            and start_time > end_time
        ):
            raise ValueError(
                "start_time cannot be greater than end_time."
            )

    # ------------------------------------------------------------------
    # Pagination utilities
    # ------------------------------------------------------------------

    @classmethod
    def _find_last_timestamp(
        cls,
        records: Sequence[Mapping[str, Any]],
    ) -> Optional[int]:
        """
        Find the greatest recognizable timestamp in a page.
        """

        timestamps: List[int] = []

        for record in records:
            value = cls._extract_record_timestamp(
                record
            )

            if value is not None:
                timestamps.append(value)

        if not timestamps:
            return None

        return max(timestamps)

    @staticmethod
    def _extract_record_timestamp(
        record: Mapping[str, Any],
    ) -> Optional[int]:
        """
        Extract a timestamp from a raw liquidation record.

        This is only used for pagination. Full normalization belongs
        to parser.py.
        """

        for field in (
            "time",
            "timestamp",
            "T",
            "updateTime",
            "update_time",
        ):
            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            if isinstance(value, bool):
                continue

            try:
                timestamp = int(float(value))
            except (
                TypeError,
                ValueError,
            ):
                continue

            if timestamp < 100_000_000_000:
                timestamp *= 1000

            return timestamp

        return None

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    def _deduplicate_records(
        self,
        records: Sequence[Mapping[str, Any]],
    ) -> List[Mapping[str, Any]]:
        """
        Remove duplicate raw records when configured to do so.

        Timestamp plus symbol/order identifier is preferred when
        available. If no unique identifier exists, the serialized
        record representation is used as a fallback.
        """

        deduplicate = bool(
            getattr(
                self.config,
                "deduplicate_records",
                True,
            )
        )

        if not deduplicate:
            return list(records)

        unique: List[Mapping[str, Any]] = []
        seen: set[Any] = set()

        for record in records:
            key = self._record_key(
                record
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(record)

        return unique

    @classmethod
    def _record_key(
        cls,
        record: Mapping[str, Any],
    ) -> Any:
        """
        Build a stable key for a raw liquidation record.
        """

        symbol = (
            record.get("symbol")
            or record.get("s")
        )

        order_id = (
            record.get("orderId")
            or record.get("order_id")
            or record.get("id")
        )

        timestamp = cls._extract_record_timestamp(
            record
        )

        if order_id is not None:
            return (
                symbol,
                order_id,
            )

        if timestamp is not None:
            return (
                symbol,
                timestamp,
                record.get("side"),
                record.get("price"),
                record.get("quantity"),
                record.get("qty"),
            )

        try:
            return (
                "record",
                tuple(
                    sorted(
                        (
                            str(key),
                            repr(value),
                        )
                        for key, value in record.items()
                    )
                ),
            )
        except Exception:
            return (
                "object",
                id(record),
            )