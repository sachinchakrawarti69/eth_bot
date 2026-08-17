"""
Trades Parser

Transforms exchange-specific raw trade responses into
standardized trade records for the ETH Bot data pipeline.

Responsibilities:
    - Parse REST trade responses
    - Parse WebSocket trade events
    - Normalize field names
    - Normalize timestamps
    - Convert numeric values
    - Produce standardized trade records

This module does not:
    - Collect data
    - Validate business rules
    - Store data
    - Calculate indicators
    - Generate ML features
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping


class TradesParser:
    """
    Parser for exchange trade data.

    The parser normalizes exchange-specific responses into
    a common internal representation.
    """

    parser_name = "trades_parser"
    parser_version = "1.0"

    # ==========================================================
    # Public API
    # ==========================================================

    def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse raw exchange trade data.

        Parameters
        ----------
        raw_data:
            Raw response returned by REST or WebSocket transport.

        Returns
        -------
        list[dict]
            Standardized trade records.
        """

        if raw_data is None:
            return []

        if isinstance(raw_data, Mapping):
            return self._parse_mapping_response(raw_data)

        if isinstance(raw_data, list):
            return self._parse_list_response(raw_data)

        raise TypeError(
            f"Unsupported trade response type: "
            f"{type(raw_data).__name__}"
        )

    # ==========================================================
    # REST Parsing
    # ==========================================================

    def parse_rest(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse REST API trade responses.
        """

        return self.parse(raw_data)

    # ==========================================================
    # WebSocket Parsing
    # ==========================================================

    def parse_websocket(self, raw_event: Mapping[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse a WebSocket trade event.
        """

        payload = raw_event.get("data", raw_event)

        if isinstance(payload, Mapping):
            return [self._normalize_mapping(payload)]

        raise TypeError(
            "Unsupported WebSocket trade payload."
        )

    # ==========================================================
    # Mapping Response
    # ==========================================================

    def _parse_mapping_response(
        self,
        raw_data: Mapping[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Parse a mapping-based exchange response.
        """

        # Common exchange response patterns.
        records = (
            raw_data.get("data")
            or raw_data.get("trades")
            or raw_data.get("result")
        )

        # A single trade event may itself be the payload.
        if records is None:
            return [self._normalize_mapping(raw_data)]

        if isinstance(records, Mapping):
            return [self._normalize_mapping(records)]

        if isinstance(records, list):
            return self._parse_list_response(records)

        raise TypeError(
            "Unsupported trade response payload."
        )

    # ==========================================================
    # List Response
    # ==========================================================

    def _parse_list_response(
        self,
        raw_data: Iterable[Any],
    ) -> List[Dict[str, Any]]:
        """
        Parse a list of trade records.
        """

        parsed: List[Dict[str, Any]] = []

        for record in raw_data:
            if isinstance(record, Mapping):
                parsed.append(
                    self._normalize_mapping(record)
                )

            elif isinstance(record, (list, tuple)):
                parsed.append(
                    self._parse_array_record(record)
                )

            else:
                raise TypeError(
                    "Unsupported trade record type: "
                    f"{type(record).__name__}"
                )

        return parsed

    # ==========================================================
    # Mapping Normalization
    # ==========================================================

    def _normalize_mapping(
        self,
        record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Normalize a dictionary-based trade record.
        """

        return {
            "trade_id": self._first_value(
                record,
                "trade_id",
                "tradeId",
                "id",
                "a",
            ),
            "symbol": self._first_value(
                record,
                "symbol",
                "s",
            ),
            "price": self._to_float(
                self._first_value(
                    record,
                    "price",
                    "p",
                )
            ),
            "quantity": self._to_float(
                self._first_value(
                    record,
                    "quantity",
                    "qty",
                    "q",
                )
            ),
            "timestamp": self._normalize_timestamp(
                self._first_value(
                    record,
                    "timestamp",
                    "time",
                    "T",
                    "trade_time",
                )
            ),
            "is_buyer_maker": self._to_bool(
                self._first_value(
                    record,
                    "is_buyer_maker",
                    "isBuyerMaker",
                    "m",
                )
            ),
        }

    # ==========================================================
    # Array Record Parsing
    # ==========================================================

    def _parse_array_record(
        self,
        record: List[Any] | tuple[Any, ...],
    ) -> Dict[str, Any]:
        """
        Parse an array-based trade record.

        Expected generic structure:

            [
                trade_id,
                price,
                quantity,
                timestamp,
                is_buyer_maker
            ]

        Exchange-specific array layouts should be mapped explicitly
        in the corresponding exchange adapter.
        """

        if len(record) < 4:
            raise ValueError(
                "Trade array contains insufficient fields."
            )

        return {
            "trade_id": record[0],
            "price": self._to_float(record[1]),
            "quantity": self._to_float(record[2]),
            "timestamp": self._normalize_timestamp(record[3]),
            "is_buyer_maker": (
                self._to_bool(record[4])
                if len(record) > 4
                else None
            ),
        }

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _first_value(
        record: Mapping[str, Any],
        *keys: str,
    ) -> Any:
        """
        Return the first available value from a list of keys.
        """

        for key in keys:
            if key in record:
                return record[key]

        return None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        """
        Convert a numeric value to float.
        """

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Unable to convert value to float: {value!r}"
            ) from exc

    @staticmethod
    def _to_bool(value: Any) -> bool | None:
        """
        Convert common boolean representations.
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            value_lower = value.lower()

            if value_lower in {"true", "1"}:
                return True

            if value_lower in {"false", "0"}:
                return False

        if isinstance(value, int):
            return bool(value)

        raise ValueError(
            f"Unable to convert value to bool: {value!r}"
        )

    @staticmethod
    def _normalize_timestamp(value: Any) -> datetime | None:
        """
        Convert supported timestamp representations to UTC datetime.
        """

        if value is None:
            return None

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)

            return value.astimezone(timezone.utc)

        if isinstance(value, (int, float)):
            # Treat large numeric values as milliseconds.
            if value > 10_000_000_000:
                value = value / 1000

            return datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            )

        if isinstance(value, str):
            text = value.strip()

            # Numeric timestamp represented as a string.
            try:
                numeric_value = float(text)

                return TradesParser._normalize_timestamp(
                    numeric_value
                )

            except ValueError:
                pass

            # ISO-8601 timestamp.
            normalized = text.replace("Z", "+00:00")

            parsed = datetime.fromisoformat(normalized)

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(timezone.utc)

        raise ValueError(
            f"Unsupported timestamp value: {value!r}"
        )