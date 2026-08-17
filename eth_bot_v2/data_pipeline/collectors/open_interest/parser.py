"""
Open Interest Parser

Normalizes raw exchange open-interest responses into the
internal ETH Bot open-interest schema.

Responsibilities:
    - Extract raw records from exchange responses.
    - Normalize field names.
    - Normalize timestamps.
    - Convert numeric values to appropriate Python types.
    - Preserve useful source metadata.
    - Produce parser-ready records for validation.

This module does not:
    - Make API requests.
    - Validate business/data-quality rules.
    - Calculate trading signals.
    - Calculate model features.
    - Execute trades.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional


class OpenInterestParser:
    """
    Parser for raw exchange open-interest records.

    The parser converts exchange-specific representations into
    a stable internal schema.
    """

    parser_name = "open_interest"
    parser_version = "1.0"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(
        self,
        response: Any,
    ) -> List[Dict[str, Any]]:
        """
        Parse a complete exchange response.

        Parameters
        ----------
        response:
            Raw exchange response.

        Returns
        -------
        list[dict]
            Normalized open-interest records.
        """

        records = self._extract_records(response)

        parsed: List[Dict[str, Any]] = []

        for record in records:
            parsed_record = self.parse_record(record)

            if parsed_record is not None:
                parsed.append(parsed_record)

        return parsed

    def parse_record(
        self,
        record: Mapping[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Parse one raw open-interest record.

        Returns
        -------
        dict | None
            Normalized record, or None when the input cannot
            produce a meaningful record.
        """

        if not isinstance(record, Mapping):
            raise TypeError(
                "Open-interest record must be a mapping."
            )

        timestamp = self._extract_timestamp(record)

        if timestamp is None:
            return None

        symbol = self._extract_symbol(record)

        open_interest = self._extract_open_interest(
            record
        )

        open_interest_value = self._extract_open_interest_value(
            record
        )

        record_time = datetime.fromtimestamp(
            timestamp / 1000,
            tz=timezone.utc,
        )

        parsed: Dict[str, Any] = {
            "timestamp": timestamp,
            "datetime": record_time,
            "symbol": symbol,
            "open_interest": open_interest,
            "open_interest_value": open_interest_value,
            "source": self._extract_source(record),
        }

        return self._remove_none_values(parsed)

    # ------------------------------------------------------------------
    # Response extraction
    # ------------------------------------------------------------------

    @classmethod
    def _extract_records(
        cls,
        response: Any,
    ) -> List[Mapping[str, Any]]:
        """
        Extract records from common exchange response formats.
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
            "Unsupported open-interest response type: "
            f"{type(response).__name__}"
        )

    # ------------------------------------------------------------------
    # Symbol
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_symbol(
        record: Mapping[str, Any],
    ) -> Optional[str]:
        """
        Extract the trading symbol.
        """

        value = OpenInterestParser._first_present(
            record,
            (
                "symbol",
                "s",
                "instType",
            ),
        )

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    # ------------------------------------------------------------------
    # Open interest
    # ------------------------------------------------------------------

    @classmethod
    def _extract_open_interest(
        cls,
        record: Mapping[str, Any],
    ) -> Optional[float]:
        """
        Extract total/open-interest quantity.

        Supports common exchange field names.
        """

        value = cls._first_present(
            record,
            (
                "sumOpenInterest",
                "openInterest",
                "open_interest",
                "oi",
                "openInterestAmount",
            ),
        )

        return cls._to_float(value)

    @classmethod
    def _extract_open_interest_value(
        cls,
        record: Mapping[str, Any],
    ) -> Optional[float]:
        """
        Extract open-interest notional/value when provided
        by the exchange.
        """

        value = cls._first_present(
            record,
            (
                "sumOpenInterestValue",
                "openInterestValue",
                "open_interest_value",
                "oiValue",
                "openInterestNotional",
            ),
        )

        return cls._to_float(value)

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------

    @classmethod
    def _extract_timestamp(
        cls,
        record: Mapping[str, Any],
    ) -> Optional[int]:
        """
        Extract and normalize a record timestamp.

        Output is always Unix milliseconds.
        """

        value = cls._first_present(
            record,
            (
                "timestamp",
                "time",
                "T",
                "openTime",
                "open_time",
            ),
        )

        return cls._normalize_timestamp(value)

    @staticmethod
    def _normalize_timestamp(
        value: Any,
    ) -> Optional[int]:
        """
        Convert supported timestamp representations to
        Unix milliseconds.
        """

        if value is None:
            return None

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
            return None

        try:
            timestamp = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

        if timestamp < 0:
            return None

        # Treat values below this threshold as seconds.
        if timestamp < 100_000_000_000:
            timestamp *= 1000

        return int(timestamp)

    # ------------------------------------------------------------------
    # Source
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_source(
        record: Mapping[str, Any],
    ) -> Optional[str]:
        """
        Extract source/exchange metadata when available.
        """

        value = OpenInterestParser._first_present(
            record,
            (
                "source",
                "exchange",
                "venue",
            ),
        )

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    @staticmethod
    def _first_present(
        record: Mapping[str, Any],
        fields: Iterable[str],
    ) -> Any:
        """
        Return the first field that exists and is not None.
        """

        for field in fields:
            if field in record:
                value = record[field]

                if value is not None:
                    return value

        return None

    @staticmethod
    def _to_float(
        value: Any,
    ) -> Optional[float]:
        """
        Convert a numeric value to float.

        Returns None for missing or non-numeric values.
        """

        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ):
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _remove_none_values(
        record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Remove fields whose values could not be extracted.
        """

        return {
            key: value
            for key, value in record.items()
            if value is not None
        }