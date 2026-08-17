"""
Long/Short Ratio Parser

Parses raw ETH futures long/short ratio responses into the
normalized internal schema used by the data pipeline.

Responsibilities:
    - Parse exchange API responses.
    - Normalize field names.
    - Convert numeric values to appropriate Python types.
    - Normalize timestamps to Unix milliseconds.
    - Normalize symbols and periods.
    - Preserve source metadata when available.

This module does not:
    - Make API requests.
    - Validate business/data-quality rules.
    - Calculate indicators.
    - Generate features.
    - Generate trading signals.
    - Manage risk.
    - Execute trades.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class LongShortRatioRecord:
    """
    Normalized long/short ratio record.
    """

    symbol: str
    period: str
    timestamp: int
    long_account: float
    short_account: float
    long_short_ratio: float

    source: Optional[str] = None

    event_time: Optional[int] = None


class LongShortRatioParser:
    """
    Parser for exchange long/short ratio responses.

    The parser converts exchange-specific records into the
    project's normalized schema.

    Validation beyond basic type conversion belongs to validator.py.
    """

    DEFAULT_SYMBOL = "ETHUSDT"
    DEFAULT_PERIOD = "5m"

    FIELD_ALIASES = {
        "symbol": (
            "symbol",
            "s",
        ),
        "period": (
            "period",
            "interval",
            "i",
        ),
        "timestamp": (
            "timestamp",
            "time",
            "T",
            "updateTime",
            "update_time",
        ),
        "long_account": (
            "longAccount",
            "long_account",
            "long",
            "longRatio",
        ),
        "short_account": (
            "shortAccount",
            "short_account",
            "short",
            "shortRatio",
        ),
        "long_short_ratio": (
            "longShortRatio",
            "long_short_ratio",
            "ratio",
        ),
        "event_time": (
            "eventTime",
            "event_time",
            "E",
        ),
        "source": (
            "source",
        ),
    }

    RESPONSE_KEYS = (
        "data",
        "result",
        "rows",
        "records",
    )

    def __init__(
        self,
        *,
        default_symbol: str = DEFAULT_SYMBOL,
        default_period: str = DEFAULT_PERIOD,
        source: Optional[str] = None,
        strict: bool = False,
    ) -> None:
        """
        Initialize the parser.

        Parameters
        ----------
        default_symbol:
            Symbol used when the exchange response does not provide one.

        default_period:
            Period used when the exchange response does not provide one.

        source:
            Optional source identifier attached to parsed records.

        strict:
            When True, malformed records raise immediately.
            When False, malformed records are skipped by parse_many().
        """

        self.default_symbol = self._normalize_symbol(
            default_symbol
        )

        self.default_period = self._normalize_period(
            default_period
        )

        self.source = source

        self.strict = strict

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(
        self,
        raw_record: Mapping[str, Any],
    ) -> LongShortRatioRecord:
        """
        Parse one raw exchange record.
        """

        if not isinstance(raw_record, Mapping):
            raise TypeError(
                "raw_record must be a mapping."
            )

        symbol = self._get_value(
            raw_record,
            "symbol",
        )

        period = self._get_value(
            raw_record,
            "period",
        )

        timestamp = self._get_value(
            raw_record,
            "timestamp",
        )

        long_account = self._get_value(
            raw_record,
            "long_account",
        )

        short_account = self._get_value(
            raw_record,
            "short_account",
        )

        long_short_ratio = self._get_value(
            raw_record,
            "long_short_ratio",
        )

        event_time = self._get_value(
            raw_record,
            "event_time",
        )

        source = self._get_value(
            raw_record,
            "source",
        )

        return LongShortRatioRecord(
            symbol=self._normalize_symbol(
                symbol
                if symbol is not None
                else self.default_symbol
            ),
            period=self._normalize_period(
                period
                if period is not None
                else self.default_period
            ),
            timestamp=self._normalize_timestamp(
                timestamp
            ),
            long_account=self._to_float(
                long_account,
                "long_account",
            ),
            short_account=self._to_float(
                short_account,
                "short_account",
            ),
            long_short_ratio=self._to_float(
                long_short_ratio,
                "long_short_ratio",
            ),
            source=(
                self._normalize_source(source)
                if source is not None
                else self.source
            ),
            event_time=(
                self._normalize_timestamp(
                    event_time
                )
                if event_time is not None
                else None
            ),
        )

    def parse_response(
        self,
        response: Any,
    ) -> list[LongShortRatioRecord]:
        """
        Parse a complete exchange response.

        The response may be:
            - a list of records,
            - a tuple of records,
            - a mapping containing data/records/result/rows.
        """

        records = self._extract_records(
            response
        )

        return self.parse_many(
            records
        )

    def parse_many(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> list[LongShortRatioRecord]:
        """
        Parse multiple raw records.

        In non-strict mode, malformed records are skipped.
        In strict mode, the first parsing error is raised.
        """

        parsed: list[LongShortRatioRecord] = []

        for record in records:
            try:
                parsed.append(
                    self.parse(record)
                )
            except (
                TypeError,
                ValueError,
                KeyError,
            ):
                if self.strict:
                    raise

        return parsed

    def parse_pages(
        self,
        pages: Iterable[Any],
    ) -> list[LongShortRatioRecord]:
        """
        Parse multiple paginated API responses.
        """

        parsed: list[LongShortRatioRecord] = []

        for page in pages:
            parsed.extend(
                self.parse_response(page)
            )

        return parsed

    # ------------------------------------------------------------------
    # Response extraction
    # ------------------------------------------------------------------

    def _extract_records(
        self,
        response: Any,
    ) -> list[Mapping[str, Any]]:
        """
        Extract records from a raw API response.
        """

        if response is None:
            return []

        if isinstance(response, Mapping):
            for key in self.RESPONSE_KEYS:
                value = response.get(key)

                if isinstance(
                    value,
                    (list, tuple),
                ):
                    return [
                        record
                        for record in value
                        if isinstance(
                            record,
                            Mapping,
                        )
                    ]

            if self._looks_like_record(
                response
            ):
                return [response]

            return []

        if isinstance(
            response,
            (list, tuple),
        ):
            return [
                record
                for record in response
                if isinstance(
                    record,
                    Mapping,
                )
            ]

        raise TypeError(
            "Unsupported response type: "
            f"{type(response).__name__}"
        )

    def _looks_like_record(
        self,
        record: Mapping[str, Any],
    ) -> bool:
        """
        Determine whether a mapping appears to be one record.
        """

        known_fields = {
            alias
            for aliases in self.FIELD_ALIASES.values()
            for alias in aliases
        }

        return any(
            key in record
            for key in known_fields
        )

    # ------------------------------------------------------------------
    # Field extraction
    # ------------------------------------------------------------------

    def _get_value(
        self,
        record: Mapping[str, Any],
        field_name: str,
    ) -> Any:
        """
        Retrieve a normalized field using exchange aliases.
        """

        aliases = self.FIELD_ALIASES.get(
            field_name,
            (),
        )

        for alias in aliases:
            if alias in record:
                return record[alias]

        return None

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_symbol(
        symbol: Any,
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

    @staticmethod
    def _normalize_period(
        period: Any,
    ) -> str:
        """
        Normalize an aggregation period.
        """

        if not isinstance(period, str):
            raise TypeError(
                "period must be a string."
            )

        normalized = period.strip().lower()

        if not normalized:
            raise ValueError(
                "period cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_source(
        source: Any,
    ) -> str:
        """
        Normalize source metadata.
        """

        if not isinstance(source, str):
            raise TypeError(
                "source must be a string."
            )

        normalized = source.strip()

        if not normalized:
            raise ValueError(
                "source cannot be empty."
            )

        return normalized

    # ------------------------------------------------------------------
    # Numeric conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _to_float(
        value: Any,
        field_name: str,
    ) -> float:
        """
        Convert a numeric exchange field to float.

        Numeric strings are accepted because exchanges commonly
        serialize numerical values as strings.
        """

        if value is None:
            raise ValueError(
                f"{field_name} is required."
            )

        if isinstance(value, bool):
            raise TypeError(
                f"{field_name} must be numeric."
            )

        try:
            converted = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{field_name} must be numeric."
            ) from exc

        if not isfinite(converted):
            raise ValueError(
                f"{field_name} must be finite."
            )

        return converted

    # ------------------------------------------------------------------
    # Timestamp conversion
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_timestamp(
        cls,
        value: Any,
    ) -> int:
        """
        Normalize a timestamp to Unix milliseconds.

        Supported inputs:
            - Unix milliseconds
            - Unix seconds
            - datetime
            - ISO-8601 string
        """

        if value is None:
            raise ValueError(
                "timestamp is required."
            )

        if isinstance(value, bool):
            raise TypeError(
                "timestamp must be a valid timestamp."
            )

        if isinstance(
            value,
            datetime,
        ):
            return cls._datetime_to_ms(
                value
            )

        if isinstance(
            value,
            (int, float),
        ):
            return cls._numeric_timestamp_to_ms(
                value
            )

        if isinstance(value, str):
            stripped = value.strip()

            if not stripped:
                raise ValueError(
                    "timestamp cannot be empty."
                )

            if cls._looks_numeric(
                stripped
            ):
                return cls._numeric_timestamp_to_ms(
                    float(stripped)
                )

            return cls._iso_to_ms(
                stripped
            )

        raise TypeError(
            "Unsupported timestamp type: "
            f"{type(value).__name__}"
        )

    @staticmethod
    def _numeric_timestamp_to_ms(
        value: float,
    ) -> int:
        """
        Convert numeric seconds/milliseconds to Unix milliseconds.
        """

        if not isfinite(value):
            raise ValueError(
                "timestamp must be finite."
            )

        if value < 0:
            raise ValueError(
                "timestamp cannot be negative."
            )

        # Unix seconds are currently around 10 digits.
        # Unix milliseconds are currently around 13 digits.
        if value < 100_000_000_000:
            value *= 1_000

        return int(value)

    @staticmethod
    def _datetime_to_ms(
        value: datetime,
    ) -> int:
        """
        Convert datetime to Unix milliseconds.
        """

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        timestamp = value.timestamp()

        if timestamp < 0:
            raise ValueError(
                "timestamp cannot be negative."
            )

        return int(
            timestamp * 1_000
        )

    @staticmethod
    def _iso_to_ms(
        value: str,
    ) -> int:
        """
        Parse an ISO-8601 timestamp.
        """

        normalized = value

        if normalized.endswith("Z"):
            normalized = (
                normalized[:-1]
                + "+00:00"
            )

        try:
            parsed = datetime.fromisoformat(
                normalized
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid ISO timestamp: {value}"
            ) from exc

        return LongShortRatioParser._datetime_to_ms(
            parsed
        )

    @staticmethod
    def _looks_numeric(
        value: str,
    ) -> bool:
        """
        Determine whether a string represents a numeric value.
        """

        try:
            float(value)
            return True
        except ValueError:
            return False