"""
Order Book Validator

Validates standardized order-book snapshots and incremental
depth updates produced by OrderBookParser.

Responsibilities:
    - Validate message type
    - Validate symbol
    - Validate timestamps
    - Validate update identifiers
    - Validate bid/ask levels
    - Validate price and quantity values
    - Detect invalid price levels
    - Detect crossed books in snapshots

This module does not:
    - Collect exchange data
    - Parse exchange payloads
    - Reconstruct the live order book
    - Apply incremental updates
    - Calculate order-book features
    - Store data
"""

from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Any, Dict, List, Mapping, Optional


class OrderBookValidator:
    """
    Runtime validator for standardized order-book messages.
    """

    validator_name = "orderbook_validator"
    validator_version = "1.0"

    VALID_MESSAGE_TYPES = {
        "snapshot",
        "update",
    }

    def __init__(
        self,
        *,
        reject_invalid: bool = True,
        require_symbol: bool = True,
        require_timestamp: bool = True,
        require_update_ids: bool = True,
        check_price_order: bool = True,
        check_crossed_snapshot: bool = True,
        allow_zero_quantity_updates: bool = True,
    ) -> None:
        self.reject_invalid = reject_invalid
        self.require_symbol = require_symbol
        self.require_timestamp = require_timestamp
        self.require_update_ids = require_update_ids
        self.check_price_order = check_price_order
        self.check_crossed_snapshot = check_crossed_snapshot
        self.allow_zero_quantity_updates = (
            allow_zero_quantity_updates
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def validate(
        self,
        message: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate one standardized order-book message.

        Returns
        -------
        dict
            Validated message.

        Raises
        ------
        ValueError
            When validation fails and reject_invalid=True.
        """

        errors = self.validate_message(message)

        if errors:
            if self.reject_invalid:
                raise ValueError(
                    "Order-book validation failed: "
                    + "; ".join(errors)
                )

        return dict(message)

    def validate_message(
        self,
        message: Mapping[str, Any],
    ) -> List[str]:
        """
        Return validation errors for an order-book message.
        """

        errors: List[str] = []

        if not isinstance(message, Mapping):
            return [
                "Order-book message must be a mapping."
            ]

        message_type = message.get("message_type")

        # ------------------------------------------------------
        # Message Type
        # ------------------------------------------------------

        if message_type not in self.VALID_MESSAGE_TYPES:
            errors.append(
                "message_type must be 'snapshot' "
                "or 'update'."
            )

        # ------------------------------------------------------
        # Symbol
        # ------------------------------------------------------

        symbol = message.get("symbol")

        if self.require_symbol:
            if not isinstance(symbol, str):
                errors.append(
                    "symbol must be a string."
                )

            elif not symbol.strip():
                errors.append(
                    "symbol cannot be empty."
                )

        # ------------------------------------------------------
        # Timestamp
        # ------------------------------------------------------

        timestamp = message.get("timestamp")

        if self.require_timestamp:
            if not isinstance(timestamp, datetime):
                errors.append(
                    "timestamp must be a datetime object."
                )

            elif timestamp.tzinfo is None:
                errors.append(
                    "timestamp must be timezone-aware."
                )

        # ------------------------------------------------------
        # Update Identifiers
        # ------------------------------------------------------

        errors.extend(
            self._validate_update_ids(
                message,
                message_type,
            )
        )

        # ------------------------------------------------------
        # Bids
        # ------------------------------------------------------

        bids = message.get("bids")

        errors.extend(
            self._validate_levels(
                bids,
                side="bids",
                message_type=message_type,
            )
        )

        # ------------------------------------------------------
        # Asks
        # ------------------------------------------------------

        asks = message.get("asks")

        errors.extend(
            self._validate_levels(
                asks,
                side="asks",
                message_type=message_type,
            )
        )

        # ------------------------------------------------------
        # Snapshot-Specific Checks
        # ------------------------------------------------------

        if message_type == "snapshot":
            errors.extend(
                self._validate_snapshot(
                    bids=bids,
                    asks=asks,
                )
            )

        return errors

    # ==========================================================
    # Update ID Validation
    # ==========================================================

    def _validate_update_ids(
        self,
        message: Mapping[str, Any],
        message_type: Optional[str],
    ) -> List[str]:
        errors: List[str] = []

        last_update_id = message.get(
            "last_update_id"
        )

        first_update_id = message.get(
            "first_update_id"
        )

        final_update_id = message.get(
            "final_update_id"
        )

        if message_type == "snapshot":
            if self.require_update_ids:
                if not self._is_positive_integer(
                    last_update_id
                ):
                    errors.append(
                        "Snapshot last_update_id must "
                        "be a positive integer."
                    )

            return errors

        if message_type == "update":
            if self.require_update_ids:
                if not self._is_positive_integer(
                    first_update_id
                ):
                    errors.append(
                        "Update first_update_id must "
                        "be a positive integer."
                    )

                if not self._is_positive_integer(
                    final_update_id
                ):
                    errors.append(
                        "Update final_update_id must "
                        "be a positive integer."
                    )

            if (
                self._is_positive_integer(first_update_id)
                and self._is_positive_integer(final_update_id)
                and first_update_id > final_update_id
            ):
                errors.append(
                    "first_update_id cannot be greater "
                    "than final_update_id."
                )

        return errors

    # ==========================================================
    # Level Validation
    # ==========================================================

    def _validate_levels(
        self,
        levels: Any,
        *,
        side: str,
        message_type: Optional[str],
    ) -> List[str]:
        errors: List[str] = []

        if levels is None:
            errors.append(
                f"{side} must be a list."
            )
            return errors

        if not isinstance(levels, list):
            errors.append(
                f"{side} must be a list."
            )
            return errors

        previous_price: Optional[float] = None

        for index, level in enumerate(levels):
            if not isinstance(level, Mapping):
                errors.append(
                    f"{side}[{index}] must be a mapping."
                )
                continue

            price = level.get("price")
            quantity = level.get("quantity")

            # --------------------------------------------------
            # Price
            # --------------------------------------------------

            if not self._is_positive_number(price):
                errors.append(
                    f"{side}[{index}].price must be "
                    "greater than zero."
                )

            # --------------------------------------------------
            # Quantity
            # --------------------------------------------------

            if not self._is_valid_quantity(
                quantity,
                message_type,
            ):
                errors.append(
                    f"{side}[{index}].quantity is invalid."
                )

            # --------------------------------------------------
            # Price Ordering
            # --------------------------------------------------

            if (
                self.check_price_order
                and self._is_positive_number(price)
                and previous_price is not None
            ):
                if side == "bids":
                    if price > previous_price:
                        errors.append(
                            f"{side} are not sorted "
                            "descending by price."
                        )

                elif side == "asks":
                    if price < previous_price:
                        errors.append(
                            f"{side} are not sorted "
                            "ascending by price."
                        )

            if self._is_positive_number(price):
                previous_price = price

        return errors

    # ==========================================================
    # Snapshot Validation
    # ==========================================================

    def _validate_snapshot(
        self,
        *,
        bids: Any,
        asks: Any,
    ) -> List[str]:
        errors: List[str] = []

        if not self.check_crossed_snapshot:
            return errors

        if not isinstance(bids, list):
            return errors

        if not isinstance(asks, list):
            return errors

        if not bids or not asks:
            return errors

        best_bid = bids[0].get("price")
        best_ask = asks[0].get("price")

        if not self._is_positive_number(best_bid):
            return errors

        if not self._is_positive_number(best_ask):
            return errors

        if best_bid >= best_ask:
            errors.append(
                "Snapshot contains a crossed or locked "
                "order book: best bid must be less "
                "than best ask."
            )

        return errors

    # ==========================================================
    # Quantity Validation
    # ==========================================================

    def _is_valid_quantity(
        self,
        quantity: Any,
        message_type: Optional[str],
    ) -> bool:
        if not self._is_number(quantity):
            return False

        if not isfinite(float(quantity)):
            return False

        if message_type == "update":
            if self.allow_zero_quantity_updates:
                return quantity >= 0

        return quantity > 0

    # ==========================================================
    # Numeric Helpers
    # ==========================================================

    @staticmethod
    def _is_number(
        value: Any,
    ) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )

    @classmethod
    def _is_positive_number(
        cls,
        value: Any,
    ) -> bool:
        return (
            cls._is_number(value)
            and isfinite(float(value))
            and value > 0
        )

    @staticmethod
    def _is_positive_integer(
        value: Any,
    ) -> bool:
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
        )

    # ==========================================================
    # Convenience API
    # ==========================================================

    def is_valid(
        self,
        message: Mapping[str, Any],
    ) -> bool:
        """
        Return True when the message passes validation.
        """

        return not self.validate_message(message)

    def validate_snapshot(
        self,
        message: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate that a message is a valid snapshot.
        """

        errors = self.validate_message(message)

        if message.get("message_type") != "snapshot":
            errors.append(
                "Expected message_type='snapshot'."
            )

        if errors:
            raise ValueError(
                "Invalid order-book snapshot: "
                + "; ".join(errors)
            )

        return dict(message)

    def validate_update(
        self,
        message: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate that a message is a valid incremental update.
        """

        errors = self.validate_message(message)

        if message.get("message_type") != "update":
            errors.append(
                "Expected message_type='update'."
            )

        if errors:
            raise ValueError(
                "Invalid order-book update: "
                + "; ".join(errors)
            )

        return dict(message)