"""
Long/Short Ratio Collector

Collects ETH futures long/short ratio data from an exchange REST API.

Responsibilities:
    - Request long/short ratio data.
    - Handle pagination/time ranges.
    - Normalize request parameters.
    - Delegate HTTP handling to the base REST collector.
    - Return raw exchange responses.

This module does not:
    - Parse exchange responses.
    - Validate normalized records.
    - Calculate indicators.
    - Generate trading signals.
    - Manage risk.
    - Execute trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from ..base.rest_collector import RestCollector


@dataclass(frozen=True, slots=True)
class LongShortRatioRequest:
    """
    Request configuration for a long/short ratio query.
    """

    symbol: str = "ETHUSDT"
    period: str = "5m"
    limit: int = 500
    start_time: Optional[int] = None
    end_time: Optional[int] = None


class LongShortRatioCollector(RestCollector):
    """
    REST collector for ETH futures long/short ratio data.

    The collector is intentionally responsible only for acquisition.
    Parsing and validation are handled by their respective modules.
    """

    ENDPOINT = "/futures/data/globalLongShortAccountRatio"

    DEFAULT_SYMBOL = "ETHUSDT"
    DEFAULT_PERIOD = "5m"
    DEFAULT_LIMIT = 500

    MIN_LIMIT = 1
    MAX_LIMIT = 500

    VALID_PERIODS = frozenset(
        {
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "12h",
            "1d",
        }
    )

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: float = 10.0,
        symbol: str = DEFAULT_SYMBOL,
        period: str = DEFAULT_PERIOD,
        limit: int = DEFAULT_LIMIT,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the long/short ratio collector.
        """

        super().__init__(
            base_url=base_url,
            api_key=api_key,
            api_secret=api_secret,
            timeout=timeout,
            **kwargs,
        )

        self.symbol = self._normalize_symbol(symbol)
        self.period = self._normalize_period(period)
        self.limit = self._validate_limit(limit)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect(
        self,
        *,
        symbol: Optional[str] = None,
        period: Optional[str] = None,
        limit: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Any:
        """
        Collect long/short ratio data.

        Parameters
        ----------
        symbol:
            Futures symbol. Defaults to ETHUSDT.

        period:
            Aggregation interval.

        limit:
            Maximum number of records.

        start_time:
            Start timestamp in Unix milliseconds.

        end_time:
            End timestamp in Unix milliseconds.

        Returns
        -------
        Any
            Raw exchange API response.
        """

        params = self._build_params(
            symbol=symbol,
            period=period,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )

        return self._request(
            method="GET",
            endpoint=self.ENDPOINT,
            params=params,
        )

    def collect_latest(
        self,
        *,
        symbol: Optional[str] = None,
        period: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Any:
        """
        Collect the latest long/short ratio observations.
        """

        return self.collect(
            symbol=symbol,
            period=period,
            limit=limit,
        )

    def collect_range(
        self,
        *,
        start_time: int,
        end_time: int,
        symbol: Optional[str] = None,
        period: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Any:
        """
        Collect long/short ratio data for a specific time range.
        """

        self._validate_time_range(
            start_time,
            end_time,
        )

        return self.collect(
            symbol=symbol,
            period=period,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )

    def collect_pages(
        self,
        *,
        start_time: int,
        end_time: int,
        symbol: Optional[str] = None,
        period: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Any]:
        """
        Collect multiple pages across a time range.

        Pagination is performed using the timestamp of the last
        returned observation.
        """

        self._validate_time_range(
            start_time,
            end_time,
        )

        normalized_symbol = self._normalize_symbol(
            symbol or self.symbol
        )

        normalized_period = self._normalize_period(
            period or self.period
        )

        normalized_limit = self._validate_limit(
            limit or self.limit
        )

        pages: list[Any] = []

        current_start = start_time

        while current_start < end_time:
            response = self.collect(
                symbol=normalized_symbol,
                period=normalized_period,
                limit=normalized_limit,
                start_time=current_start,
                end_time=end_time,
            )

            pages.append(response)

            records = self._extract_records(
                response
            )

            if not records:
                break

            last_timestamp = self._extract_last_timestamp(
                records
            )

            if last_timestamp is None:
                break

            next_start = last_timestamp + 1

            if next_start <= current_start:
                break

            current_start = next_start

            if len(records) < normalized_limit:
                break

        return pages

    # ------------------------------------------------------------------
    # Request construction
    # ------------------------------------------------------------------

    def _build_params(
        self,
        *,
        symbol: Optional[str],
        period: Optional[str],
        limit: Optional[int],
        start_time: Optional[int],
        end_time: Optional[int],
    ) -> dict[str, Any]:
        """
        Build exchange request parameters.
        """

        normalized_symbol = self._normalize_symbol(
            symbol or self.symbol
        )

        normalized_period = self._normalize_period(
            period or self.period
        )

        normalized_limit = self._validate_limit(
            limit or self.limit
        )

        self._validate_optional_timestamp(
            start_time,
            "start_time",
        )

        self._validate_optional_timestamp(
            end_time,
            "end_time",
        )

        if (
            start_time is not None
            and end_time is not None
            and start_time > end_time
        ):
            raise ValueError(
                "start_time cannot be greater than end_time."
            )

        params: dict[str, Any] = {
            "symbol": normalized_symbol,
            "period": normalized_period,
            "limit": normalized_limit,
        }

        if start_time is not None:
            params["startTime"] = start_time

        if end_time is not None:
            params["endTime"] = end_time

        return params

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_records(
        response: Any,
    ) -> Sequence[Mapping[str, Any]]:
        """
        Extract records from a typical REST response.

        The exchange normally returns a list directly.
        """

        if isinstance(response, list):
            return response

        if isinstance(response, tuple):
            return response

        if isinstance(response, Mapping):
            for key in (
                "data",
                "result",
                "rows",
            ):
                value = response.get(key)

                if isinstance(value, (list, tuple)):
                    return value

        return ()

    @staticmethod
    def _extract_last_timestamp(
        records: Sequence[Mapping[str, Any]],
    ) -> Optional[int]:
        """
        Extract the latest timestamp from a response page.
        """

        if not records:
            return None

        last = records[-1]

        if not isinstance(last, Mapping):
            return None

        for key in (
            "timestamp",
            "time",
            "T",
            "updateTime",
        ):
            value = last.get(key)

            if value is None:
                continue

            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return None

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        """
        Normalize a futures symbol.
        """

        if not isinstance(symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        normalized = symbol.strip().upper()

        if not normalized:
            raise ValueError(
                "symbol cannot be empty."
            )

        return normalized

    @classmethod
    def _normalize_period(
        cls,
        period: str,
    ) -> str:
        """
        Normalize and validate aggregation period.
        """

        if not isinstance(period, str):
            raise TypeError(
                "period must be a string."
            )

        normalized = period.strip().lower()

        if normalized not in cls.VALID_PERIODS:
            raise ValueError(
                "Unsupported period "
                f"'{period}'. Valid periods: "
                f"{sorted(cls.VALID_PERIODS)}"
            )

        return normalized

    @classmethod
    def _validate_limit(
        cls,
        limit: int,
    ) -> int:
        """
        Validate API result limit.
        """

        if isinstance(limit, bool):
            raise TypeError(
                "limit must be an integer."
            )

        if not isinstance(limit, int):
            raise TypeError(
                "limit must be an integer."
            )

        if not (
            cls.MIN_LIMIT
            <= limit
            <= cls.MAX_LIMIT
        ):
            raise ValueError(
                "limit must be between "
                f"{cls.MIN_LIMIT} and "
                f"{cls.MAX_LIMIT}."
            )

        return limit

    @staticmethod
    def _validate_optional_timestamp(
        value: Optional[int],
        field_name: str,
    ) -> None:
        """
        Validate an optional Unix-millisecond timestamp.
        """

        if value is None:
            return

        if isinstance(value, bool):
            raise TypeError(
                f"{field_name} must be an integer."
            )

        if not isinstance(value, int):
            raise TypeError(
                f"{field_name} must be an integer."
            )

        if value < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

    @staticmethod
    def _validate_time_range(
        start_time: int,
        end_time: int,
    ) -> None:
        """
        Validate a required time range.
        """

        LongShortRatioCollector._validate_optional_timestamp(
            start_time,
            "start_time",
        )

        LongShortRatioCollector._validate_optional_timestamp(
            end_time,
            "end_time",
        )

        if start_time > end_time:
            raise ValueError(
                "start_time cannot be greater than end_time."
            )