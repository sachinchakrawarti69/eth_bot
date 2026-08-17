"""
Trades Validator

Validates standardized trade records produced by TradesParser.

Responsibilities:
    - Validate required fields
    - Validate data types
    - Validate timestamps
    - Validate price and quantity
    - Validate trade identifiers
    - Detect duplicate trades
    - Validate chronological ordering

This module does not:
    - Collect exchange data
    - Parse exchange responses
    - Store data
    - Calculate indicators
    - Generate features
    - Execute trades
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional


class TradesValidator:
    """
    Runtime validator for standardized trade records.
    """

    validator_name = "trades_validator"
    validator_version = "1.0"

    REQUIRED_FIELDS = {
        "trade_id",
        "price",
        "quantity",
        "timestamp",
    }

    OPTIONAL_FIELDS = {
        "symbol",
        "is_buyer_maker",
    }

    def __init__(
        self,
        *,
        reject_invalid: bool = True,
        detect_duplicates: bool = True,
        validate_order: bool = True,
        allow_empty: bool = True,
    ) -> None:
        self.reject_invalid = reject_invalid
        self.detect_duplicates = detect_duplicates
        self.validate_order = validate_order
        self.allow_empty = allow_empty

    # ==========================================================
    # Public API
    # ==========================================================

    def validate(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Validate a collection of trade records.

        Parameters
        ----------
        records:
            Iterable containing standardized trade records.

        Returns
        -------
        list[dict]
            Validated trade records.

        Raises
        ------
        ValueError
            If validation fails and reject_invalid=True.
        """

        if records is None:
            if self.allow_empty:
                return []

            raise ValueError(
                "Trade records cannot be None."
            )

        validated: List[Dict[str, Any]] = []

        seen_trade_ids: set[Any] = set()

        previous_timestamp: Optional[datetime] = None

        for index, record in enumerate(records):
            normalized = dict(record)

            errors = self.validate_record(
                normalized,
                index=index,
            )

            if self.detect_duplicates:
                trade_id = normalized.get("trade_id")

                if trade_id in seen_trade_ids:
                    errors.append(
                        f"Duplicate trade_id: {trade_id!r}"
                    )
                else:
                    seen_trade_ids.add(trade_id)

            if self.validate_order:
                timestamp = normalized.get("timestamp")

                if (
                    timestamp is not None
                    and previous_timestamp is not None
                    and timestamp < previous_timestamp
                ):
                    errors.append(
                        "Trade timestamps are not "
                        "chronologically ordered."
                    )

                if timestamp is not None:
                    previous_timestamp = timestamp

            if errors:
                if self.reject_invalid:
                    raise ValueError(
                        self._format_errors(
                            index=index,
                            errors=errors,
                        )
                    )

                continue

            validated.append(normalized)

        return validated

    # ==========================================================
    # Single Record Validation
    # ==========================================================

    def validate_record(
        self,
        record: Mapping[str, Any],
        *,
        index: Optional[int] = None,
    ) -> List[str]:
        """
        Validate one standardized trade record.

        Returns
        -------
        list[str]
            Validation errors. An empty list means valid.
        """

        errors: List[str] = []

        # ------------------------------------------------------
        # Required fields
        # ------------------------------------------------------

        missing_fields = self.REQUIRED_FIELDS - record.keys()

        if missing_fields:
            errors.append(
                "Missing required fields: "
                + ", ".join(sorted(missing_fields))
            )

        # ------------------------------------------------------
        # Trade ID
        # ------------------------------------------------------

        trade_id = record.get("trade_id")

        if trade_id is not None:
            if isinstance(trade_id, bool):
                errors.append(
                    "trade_id must not be boolean."
                )

            elif not isinstance(
                trade_id,
                (int, str),
            ):
                errors.append(
                    "trade_id must be an integer or string."
                )

            elif isinstance(trade_id, str) and not trade_id.strip():
                errors.append(
                    "trade_id cannot be empty."
                )

        # ------------------------------------------------------
        # Symbol
        # ------------------------------------------------------

        symbol = record.get("symbol")

        if symbol is not None:
            if not isinstance(symbol, str):
                errors.append(
                    "symbol must be a string."
                )

            elif not symbol.strip():
                errors.append(
                    "symbol cannot be empty."
                )

        # ------------------------------------------------------
        # Price
        # ------------------------------------------------------

        price = record.get("price")

        if not self._is_number(price):
            errors.append(
                "price must be numeric."
            )

        elif price <= 0:
            errors.append(
                "price must be greater than zero."
            )

        # ------------------------------------------------------
        # Quantity
        # ------------------------------------------------------

        quantity = record.get("quantity")

        if not self._is_number(quantity):
            errors.append(
                "quantity must be numeric."
            )

        elif quantity <= 0:
            errors.append(
                "quantity must be greater than zero."
            )

        # ------------------------------------------------------
        # Timestamp
        # ------------------------------------------------------

        timestamp = record.get("timestamp")

        if not isinstance(timestamp, datetime):
            errors.append(
                "timestamp must be a datetime object."
            )

        elif timestamp.tzinfo is None:
            errors.append(
                "timestamp must be timezone-aware."
            )

        # ------------------------------------------------------
        # Buyer/Maker Flag
        # ------------------------------------------------------

        is_buyer_maker = record.get(
            "is_buyer_maker"
        )

        if is_buyer_maker is not None:
            if not isinstance(
                is_buyer_maker,
                bool,
            ):
                errors.append(
                    "is_buyer_maker must be boolean."
                )

        return errors

    # ==========================================================
    # Convenience Methods
    # ==========================================================

    def is_valid(
        self,
        record: Mapping[str, Any],
    ) -> bool:
        """
        Return True when a record passes validation.
        """

        return not self.validate_record(record)

    def validate_one(
        self,
        record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate and return one trade record.
        """

        errors = self.validate_record(record)

        if errors:
            raise ValueError(
                self._format_errors(
                    index=None,
                    errors=errors,
                )
            )

        return dict(record)

    # ==========================================================
    # Numeric Validation
    # ==========================================================

    @staticmethod
    def _is_number(value: Any) -> bool:
        """
        Check whether a value is a valid numeric value.

        Boolean values are intentionally excluded because bool
        is a subclass of int in Python.
        """

        return isinstance(
            value,
            (int, float),
        ) and not isinstance(
            value,
            bool,
        )

    # ==========================================================
    # Error Formatting
    # ==========================================================

    @staticmethod
    def _format_errors(
        *,
        index: Optional[int],
        errors: List[str],
    ) -> str:
        """
        Format validation errors into one readable message.
        """

        location = (
            f" at index {index}"
            if index is not None
            else ""
        )

        return (
            f"Trade validation failed{location}: "
            + "; ".join(errors)
        )