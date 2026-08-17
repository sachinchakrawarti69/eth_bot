"""
Order Book Parser

Transforms exchange-specific order-book snapshots and depth
updates into a standardized internal representation.

Responsibilities:
    - Parse REST order-book snapshots
    - Parse WebSocket depth updates
    - Normalize bids and asks
    - Convert price and quantity values to numeric types
    - Normalize timestamps
    - Preserve update identifiers

This module does not:
    - Collect data
    - Validate business rules
    - Reconstruct the complete order book
    - Store data
    - Calculate order-book features
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional


class OrderBookParser:
    """
    Parser for exchange order-book snapshots and depth updates.
    """

    parser_name = "orderbook_parser"
    parser_version = "1.0"

    # ==========================================================
    # Public API
    # ==========================================================

    def parse(
        self,
        raw_data: Any,
        *,
        message_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parse an order-book response.

        Parameters
        ----------
        raw_data:
            Raw exchange response.

        message_type:
            Optional explicit message type:
                - snapshot
                - update

        Returns
        -------
        dict
            Standardized order-book message.
        """

        if raw_data is None:
            raise ValueError(
                "Order-book data cannot be None."
            )

        payload = self._unwrap_payload(raw_data)

        if message_type is None:
            message_type = self._detect_message_type(
                payload
            )

        if message_type == "snapshot":
            return self.parse_snapshot(payload)

        if message_type == "update":
            return self.parse_update(payload)

        raise ValueError(
            f"Unsupported order-book message type: "
            f"{message_type!r}"
        )

    # ==========================================================
    # Snapshot
    # ==========================================================

    def parse_snapshot(
        self,
        raw_data: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Parse a REST order-book snapshot.
        """

        return {
            "message_type": "snapshot",
            "symbol": self._first_value(
                raw_data,
                "symbol",
                "s",
            ),
            "timestamp": self._normalize_timestamp(
                self._first_value(
                    raw_data,
                    "timestamp",
                    "time",
                    "T",
                )
            ),
            "last_update_id": self._to_int(
                self._first_value(
                    raw_data,
                    "last_update_id",
                    "lastUpdateId",
                )
            ),
            "first_update_id": None,
            "final_update_id": None,
            "bids": self._parse_levels(
                self._first_value(
                    raw_data,
                    "bids",
                    "b",
                )
            ),
            "asks": self._parse_levels(
                self._first_value(
                    raw_data,
                    "asks",
                    "a",
                )
            ),
        }

    # ==========================================================
    # Incremental Update
    # ==========================================================

    def parse_update(
        self,
        raw_data: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Parse a WebSocket incremental depth update.
        """

        return {
            "message_type": "update",
            "symbol": self._first_value(
                raw_data,
                "symbol",
                "s",
            ),
            "timestamp": self._normalize_timestamp(
                self._first_value(
                    raw_data,
                    "timestamp",
                    "event_time",
                    "time",
                    "E",
                )
            ),
            "last_update_id": self._to_int(
                self._first_value(
                    raw_data,
                    "last_update_id",
                    "lastUpdateId",
                )
            ),
            "first_update_id": self._to_int(
                self._first_value(
                    raw_data,
                    "first_update_id",
                    "firstUpdateId",
                    "U",
                )
            ),
            "final_update_id": self._to_int(
                self._first_value(
                    raw_data,
                    "final_update_id",
                    "finalUpdateId",
                    "u",
                )
            ),
            "bids": self._parse_levels(
                self._first_value(
                    raw_data,
                    "bids",
                    "bid_updates",
                    "b",
            )
            ),
            "asks": self._parse_levels(
                self._first_value(
                    raw_data,
                    "asks",
                    "ask_updates",
                    "a",
                )
            ),
        }

    # ==========================================================
    # Level Parsing
    # ==========================================================

    def _parse_levels(
        self,
        levels: Any,
    ) -> List[Dict[str, float]]:
        """
        Normalize bid/ask levels.

        Expected level structure:

            [price, quantity]

        or:

            {
                "price": ...,
                "quantity": ...
            }
        """

        if levels is None:
            return []

        if not isinstance(levels, list):
            raise TypeError(
                "Order-book levels must be a list."
            )

        parsed: List[Dict[str, float]] = []

        for level in levels:
            if isinstance(level, Mapping):
                price = self._first_value(
                    level,
                    "price",
                    "p",
                )

                quantity = self._first_value(
                    level,
                    "quantity",
                    "qty",
                    "q",
                )

            elif isinstance(level, (list, tuple)):
                if len(level) < 2:
                    raise ValueError(
                        "Order-book level must contain "
                        "price and quantity."
                    )

                price = level[0]
                quantity = level[1]

            else:
                raise TypeError(
                    "Unsupported order-book level type: "
                    f"{type(level).__name__}"
                )

            parsed.append(
                {
                    "price": self._to_float(price),
                    "quantity": self._to_float(quantity),
                }
            )

        return parsed

    # ==========================================================
    # Payload Handling
    # ==========================================================

    def _unwrap_payload(
        self,
        raw_data: Any,
    ) -> Mapping[str, Any]:
        """
        Extract the actual exchange payload from an event
        envelope.
        """

        if not isinstance(raw_data, Mapping):
            raise TypeError(
                "Order-book response must be a mapping."
            )

        payload = raw_data.get(
            "data",
            raw_data,
        )

        if not isinstance(payload, Mapping):
            raise TypeError(
                "Order-book payload must be a mapping."
            )

        return payload

    # ==========================================================
    # Message Detection
    # ==========================================================

    @staticmethod
    def _detect_message_type(
        payload: Mapping[str, Any],
    ) -> str:
        """
        Detect whether a payload represents a snapshot
        or incremental update.
        """

        if (
            "first_update_id" in payload
            or "firstUpdateId" in payload
            or "U" in payload
        ):
            return "update"

        if (
            "last_update_id" in payload
            or "lastUpdateId" in payload
        ):
            return "snapshot"

        if "bids" in payload and "asks" in payload:
            return "snapshot"

        raise ValueError(
            "Unable to determine order-book message type."
        )

    # ==========================================================
    # Generic Helpers
    # ==========================================================

    @staticmethod
    def _first_value(
        record: Mapping[str, Any],
        *keys: str,
    ) -> Any:
        """
        Return the first available field.
        """

        for key in keys:
            if key in record:
                return record[key]

        return None

    @staticmethod
    def _to_float(
        value: Any,
    ) -> float:
        """
        Convert a value to float.
        """

        if value is None:
            raise ValueError(
                "Order-book numeric value cannot be None."
            )

        try:
            return float(value)

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid numeric value: {value!r}"
            ) from exc

    @staticmethod
    def _to_int(
        value: Any,
    ) -> Optional[int]:
        """
        Convert a value to integer.
        """

        if value is None:
            return None

        try:
            return int(value)

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid integer value: {value!r}"
            ) from exc

    @staticmethod
    def _normalize_timestamp(
        value: Any,
    ) -> Optional[datetime]:
        """
        Normalize timestamps to UTC-aware datetime.
        """

        if value is None:
            return None

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(
                    tzinfo=timezone.utc
                )

            return value.astimezone(
                timezone.utc
            )

        if isinstance(value, (int, float)):
            # Milliseconds are generally much larger than
            # Unix seconds.
            if value > 10_000_000_000:
                value = value / 1000

            return datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            )

        if isinstance(value, str):
            text = value.strip()

            try:
                numeric_value = float(text)

                return OrderBookParser._normalize_timestamp(
                    numeric_value
                )

            except ValueError:
                pass

            normalized = text.replace(
                "Z",
                "+00:00",
            )

            parsed = datetime.fromisoformat(
                normalized
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(
                timezone.utc
            )

        raise ValueError(
            f"Unsupported timestamp: {value!r}"
        )