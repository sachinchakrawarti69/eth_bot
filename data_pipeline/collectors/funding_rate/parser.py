"""
Funding Rate Parser

Transforms raw exchange funding-rate responses into the
standardized funding-rate schema used by the data pipeline.

Responsibilities:
    - Parse raw exchange records.
    - Normalize field names.
    - Normalize timestamps.
    - Normalize numeric values.
    - Preserve relevant exchange metadata.

This module does not:
    - Collect data.
    - Validate business rules.
    - Store data.
    - Calculate features.
    - Generate trading signals.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Mapping, Optional


class FundingRateParser:
    """
    Parser for raw perpetual-futures funding-rate records.
    """

    parser_name = "funding_rate"
    parser_version = "1.0"

    SYMBOL_FIELDS = (
        "symbol",
        "s",
        "instrument",
        "instId",
    )

    FUNDING_RATE_FIELDS = (
        "fundingRate",
        "funding_rate",
        "r",
    )

    FUNDING_TIME_FIELDS = (
        "fundingTime",
        "funding_time",
        "timestamp",
        "time",
        "T",
    )

    MARK_PRICE_FIELDS = (
        "markPrice",
        "mark_price",
        "p",
    )

    EXCHANGE_FIELDS = (
        "exchange",
        "source",
    )

    def parse(
        self,
        records: Any,
    ) -> List[Dict[str, Any]]:
        """
        Parse a collection of raw funding-rate records.

        Parameters
        ----------
        records:
            Raw exchange response or iterable of raw records.

        Returns
        -------
        list[dict]
            Standardized funding-rate records.
        """

        raw_records = self._normalize_input(records)

        parsed: List[Dict[str, Any]] = []

        for record in raw_records:
            parsed_record = self.parse_record(record)

            if parsed_record is not None:
                parsed.append(parsed_record)

        return parsed

    def parse_record(
        self,
        record: Mapping[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Parse one raw funding-rate record.

        Returns None when the record cannot be converted into
        a meaningful standardized record.
        """

        if not isinstance(record, Mapping):
            raise TypeError(
                "Funding-rate record must be a mapping."
            )

        symbol = self._first_value(
            record,
            self.SYMBOL_FIELDS,
        )

        funding_rate = self._first_value(
            record,
            self.FUNDING_RATE_FIELDS,
        )

        funding_time = self._first_value(
            record,
            self.FUNDING_TIME_FIELDS,
        )

        mark_price = self._first_value(
            record,
            self.MARK_PRICE_FIELDS,
        )

        exchange = self._first_value(
            record,
            self.EXCHANGE_FIELDS,
        )

        parsed: Dict[str, Any] = {
            "symbol": self._parse_symbol(symbol),
            "funding_rate": self._parse_decimal(
                funding_rate
            ),
            "funding_time": self._parse_timestamp(
                funding_time
            ),
        }

        if mark_price is not None:
            parsed["mark_price"] = self._parse_decimal(
                mark_price
            )

        if exchange is not None:
            parsed["exchange"] = str(exchange)

        return parsed

    @staticmethod
    def _normalize_input(
        records: Any,
    ) -> List[Mapping[str, Any]]:
        """
        Normalize different API response containers into a list.
        """

        if records is None:
            return []

        if isinstance(records, Mapping):
            for key in (
                "data",
                "result",
                "rows",
                "list",
            ):
                value = records.get(key)

                if isinstance(value, list):
                    return [
                        item
                        for item in value
                        if isinstance(item, Mapping)
                    ]

            return [records]

        if isinstance(records, (list, tuple)):
            return [
                item
                for item in records
                if isinstance(item, Mapping)
            ]

        if isinstance(records, Iterable):
            return [
                item
                for item in records
                if isinstance(item, Mapping)
            ]

        raise TypeError(
            "Unsupported funding-rate input type: "
            f"{type(records).__name__}"
        )

    @staticmethod
    def _first_value(
        record: Mapping[str, Any],
        fields: Iterable[str],
    ) -> Any:
        """
        Return the first available field value.
        """

        for field in fields:
            if field in record:
                value = record[field]

                if value is not None:
                    return value

        return None

    @staticmethod
    def _parse_symbol(
        value: Any,
    ) -> Optional[str]:
        """
        Normalize a trading symbol.
        """

        if value is None:
            return None

        symbol = str(value).strip()

        return symbol or None

    @staticmethod
    def _parse_decimal(
        value: Any,
    ) -> Optional[float]:
        """
        Convert numeric exchange values to float.

        Decimal is used during conversion to avoid relying on
        implicit string arithmetic.
        """

        if value is None:
            return None

        if isinstance(value, bool):
            raise ValueError(
                "Boolean values are not valid numeric values."
            )

        if isinstance(value, Decimal):
            return float(value)

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError(
                f"Unable to parse numeric value: {value!r}"
            ) from exc

        if not decimal_value.is_finite():
            raise ValueError(
                f"Numeric value must be finite: {value!r}"
            )

        return float(decimal_value)

    @classmethod
    def _parse_timestamp(
        cls,
        value: Any,
    ) -> Optional[int]:
        """
        Normalize a timestamp to Unix milliseconds.
        """

        if value is None:
            return None

        if isinstance(value, datetime):
            return cls._datetime_to_milliseconds(value)

        if isinstance(value, bool):
            raise ValueError(
                "Boolean values are not valid timestamps."
            )

        if isinstance(value, (int, float, Decimal)):
            return cls._numeric_timestamp_to_milliseconds(
                value
            )

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

            try:
                return cls._numeric_timestamp_to_milliseconds(
                    Decimal(value)
                )
            except (InvalidOperation, ValueError):
                return cls._iso_timestamp_to_milliseconds(
                    value
                )

        raise TypeError(
            "Unsupported timestamp type: "
            f"{type(value).__name__}"
        )

    @staticmethod
    def _numeric_timestamp_to_milliseconds(
        value: Any,
    ) -> int:
        """
        Convert a numeric timestamp into Unix milliseconds.

        Values below 1e11 are treated as Unix seconds.
        Larger values are treated as milliseconds.
        """

        numeric_value = float(value)

        if numeric_value < 0:
            raise ValueError(
                "Timestamp cannot be negative."
            )

        if numeric_value < 100_000_000_000:
            numeric_value *= 1000

        return int(numeric_value)

    @staticmethod
    def _datetime_to_milliseconds(
        value: datetime,
    ) -> int:
        """
        Convert datetime to Unix milliseconds.
        """

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        return int(
            value.timestamp() * 1000
        )

    @staticmethod
    def _iso_timestamp_to_milliseconds(
        value: str,
    ) -> int:
        """
        Parse an ISO-8601 timestamp into Unix milliseconds.
        """

        normalized = value

        if normalized.endswith("Z"):
            normalized = (
                normalized[:-1] + "+00:00"
            )

        try:
            parsed = datetime.fromisoformat(
                normalized
            )
        except ValueError as exc:
            raise ValueError(
                f"Unable to parse timestamp: {value!r}"
            ) from exc

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return int(
            parsed.timestamp() * 1000
        )