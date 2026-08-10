"""
Liquidations Parser

Normalizes raw exchange liquidation records into the internal
ETH futures liquidation schema.

Responsibilities:
    - Parse raw exchange liquidation records.
    - Normalize exchange-specific field names.
    - Convert numeric fields to appropriate Python types.
    - Normalize timestamps to Unix milliseconds.
    - Normalize liquidation side.
    - Preserve useful source metadata.

This module does not:
    - Make API requests.
    - Validate business rules.
    - Calculate indicators.
    - Generate trading signals.
    - Execute trades.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Optional


class LiquidationParser:
    """
    Parser for raw ETH futures liquidation records.

    The parser converts exchange-specific records into a consistent
    internal representation suitable for validation and storage.
    """

    parser_name = "liquidations"
    parser_version = "1.0"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(
        self,
        record: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Parse one raw liquidation record.

        Parameters
        ----------
        record:
            Raw exchange liquidation record.

        Returns
        -------
        dict[str, Any]
            Normalized liquidation record.
        """

        if not isinstance(record, Mapping):
            raise TypeError(
                "record must be a mapping."
            )

        return {
            "symbol": self._parse_symbol(record),
            "side": self._parse_side(record),
            "order_id": self._parse_order_id(record),
            "price": self._parse_float(
                self._first(
                    record,
                    (
                        "price",
                        "p",
                    ),
                )
            ),
            "quantity": self._parse_float(
                self._first(
                    record,
                    (
                        "quantity",
                        "qty",
                        "q",
                    ),
                )
            ),
            "quote_quantity": self._parse_float(
                self._first(
                    record,
                    (
                        "quoteQuantity",
                        "quote_quantity",
                        "quoteQty",
                        "notional",
                    ),
                )
            ),
            "timestamp": self._parse_timestamp(
                self._first(
                    record,
                    (
                        "time",
                        "timestamp",
                        "T",
                        "updateTime",
                        "update_time",
                    ),
                )
            ),
            "event_time": self._parse_timestamp(
                self._first(
                    record,
                    (
                        "eventTime",
                        "event_time",
                        "E",
                    ),
                )
            ),
            "source": self._parse_source(
                record
            ),
        }

    def parse_many(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Parse multiple raw liquidation records.

        Parameters
        ----------
        records:
            Iterable containing raw exchange records.

        Returns
        -------
        list[dict[str, Any]]
            List of normalized records.
        """

        if records is None:
            raise ValueError(
                "records cannot be None."
            )

        return [
            self.parse(record)
            for record in records
        ]

    # ------------------------------------------------------------------
    # Symbol
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_symbol(
        record: Mapping[str, Any],
    ) -> Optional[str]:
        """
        Parse and normalize the trading symbol.
        """

        value = LiquidationParser._first(
            record,
            (
                "symbol",
                "s",
            ),
        )

        if value is None:
            return None

        value = str(value).strip()

        return value.upper() if value else None

    # ------------------------------------------------------------------
    # Side
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_side(
        record: Mapping[str, Any],
    ) -> Optional[str]:
        """
        Normalize liquidation/order side.

        Accepted normalized values:
            BUY
            SELL
        """

        value = LiquidationParser._first(
            record,
            (
                "side",
                "S",
                "orderSide",
                "order_side",
            ),
        )

        if value is None:
            return None

        side = str(value).strip().upper()

        aliases = {
            "B": "BUY",
            "BUY": "BUY",
            "LONG": "BUY",
            "OPEN_LONG": "BUY",
            "SELL": "SELL",
            "S": "SELL",
            "SHORT": "SELL",
            "OPEN_SHORT": "SELL",
        }

        return aliases.get(
            side,
            side,
        )

    # ------------------------------------------------------------------
    # Order ID
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_order_id(
        record: Mapping[str, Any],
    ) -> Optional[str]:
        """
        Normalize the liquidation/order identifier.
        """

        value = LiquidationParser._first(
            record,
            (
                "orderId",
                "order_id",
                "id",
                "i",
            ),
        )

        if value is None:
            return None

        return str(value)

    # ------------------------------------------------------------------
    # Numeric parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_float(
        value: Any,
    ) -> Optional[float]:
        """
        Convert a numeric exchange value to float.

        None and empty strings become None.
        """

        if value is None:
            return None

        if isinstance(value, bool):
            raise TypeError(
                "Boolean values cannot be parsed as numeric values."
            )

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"Unable to parse numeric value: {value!r}"
            ) from exc

    # ------------------------------------------------------------------
    # Timestamp parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(
        value: Any,
    ) -> Optional[int]:
        """
        Normalize timestamps to Unix milliseconds.

        Supported inputs:
            - Unix seconds
            - Unix milliseconds
            - datetime
            - ISO-8601 datetime string
        """

        if value is None:
            return None

        if isinstance(value, datetime):
            return LiquidationParser._datetime_to_ms(
                value
            )

        if isinstance(value, bool):
            raise TypeError(
                "Boolean values cannot be used as timestamps."
            )

        if isinstance(value, (int, float)):
            return LiquidationParser._numeric_timestamp_to_ms(
                value
            )

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

            # Numeric timestamp represented as text.
            try:
                numeric_value = float(value)

                return LiquidationParser._numeric_timestamp_to_ms(
                    numeric_value
                )
            except ValueError:
                pass

            return LiquidationParser._iso_datetime_to_ms(
                value
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
        Convert numeric seconds or milliseconds to milliseconds.
        """

        if value < 0:
            raise ValueError(
                "Timestamp cannot be negative."
            )

        if value < 100_000_000_000:
            return int(value * 1000)

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

        return int(
            value.timestamp() * 1000
        )

    @staticmethod
    def _iso_datetime_to_ms(
        value: str,
    ) -> int:
        """
        Parse an ISO-8601 datetime string.
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

        return LiquidationParser._datetime_to_ms(
            parsed
        )

    # ------------------------------------------------------------------
    # Source metadata
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_source(
        record: Mapping[str, Any],
    ) -> Optional[str]:
        """
        Extract the source/exchange identifier when available.
        """

        value = LiquidationParser._first(
            record,
            (
                "source",
                "exchange",
                "exchange_name",
            ),
        )

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _first(
        record: Mapping[str, Any],
        fields: tuple[str, ...],
    ) -> Any:
        """
        Return the first available field from a record.

        A field with value None is treated as unavailable.
        """

        for field in fields:
            if field in record:
                value = record[field]

                if value is not None:
                    return value

        return None