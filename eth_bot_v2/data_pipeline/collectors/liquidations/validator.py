"""
Liquidations Validator

Validates normalized ETH futures liquidation records.

Responsibilities:
    - Validate record structure.
    - Validate required fields.
    - Validate field types.
    - Validate numeric values.
    - Validate timestamps.
    - Validate symbol.
    - Validate liquidation side.
    - Validate duplicate records when requested.

This module does not:
    - Collect data.
    - Parse exchange-specific fields.
    - Calculate indicators.
    - Generate trading signals.
    - Manage risk.
    - Execute trades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Iterable, Mapping, Optional


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """
    Represents one validation issue.
    """

    field: str
    message: str
    value: Any = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Result of validating one liquidation record.
    """

    valid: bool
    issues: tuple[ValidationIssue, ...] = field(
        default_factory=tuple
    )

    def raise_if_invalid(self) -> None:
        """
        Raise ValueError when the record is invalid.
        """

        if self.valid:
            return

        messages = "; ".join(
            f"{issue.field}: {issue.message}"
            for issue in self.issues
        )

        raise ValueError(
            f"Invalid liquidation record: {messages}"
        )


class LiquidationValidator:
    """
    Validator for normalized ETH futures liquidation records.

    Validation is intentionally separate from parsing.

    Parser:
        Converts exchange data into the internal schema.

    Validator:
        Determines whether the normalized record satisfies
        the schema and configured data-quality rules.
    """

    validator_name = "liquidations"
    validator_version = "1.0"

    DEFAULT_REQUIRED_FIELDS = (
        "symbol",
        "side",
        "price",
        "quantity",
        "timestamp",
    )

    VALID_SIDES = frozenset(
        {
            "BUY",
            "SELL",
        }
    )

    def __init__(
        self,
        *,
        expected_symbol: str = "ETHUSDT",
        required_fields: Optional[
            Iterable[str]
        ] = None,
        allow_unknown_side: bool = False,
        allow_missing_order_id: bool = True,
        allow_missing_quote_quantity: bool = True,
        allow_missing_event_time: bool = True,
        enforce_finite_numbers: bool = True,
        enforce_positive_price: bool = True,
        enforce_positive_quantity: bool = True,
        enforce_non_negative_quote_quantity: bool = True,
        enforce_timestamp_range: bool = True,
        max_future_ms: int = 60_000,
    ) -> None:
        """
        Initialize the validator.

        Parameters
        ----------
        expected_symbol:
            Expected futures instrument.

        required_fields:
            Fields that must be present and non-None.

        allow_unknown_side:
            Whether sides outside BUY/SELL are accepted.

        allow_missing_order_id:
            Whether order_id may be None.

        allow_missing_quote_quantity:
            Whether quote_quantity may be None.

        allow_missing_event_time:
            Whether event_time may be None.

        enforce_finite_numbers:
            Reject NaN and infinity.

        enforce_positive_price:
            Require price > 0.

        enforce_positive_quantity:
            Require quantity > 0.

        enforce_non_negative_quote_quantity:
            Require quote_quantity >= 0.

        enforce_timestamp_range:
            Reject timestamps too far in the future.

        max_future_ms:
            Allowed future timestamp tolerance.
        """

        if not isinstance(
            expected_symbol,
            str,
        ):
            raise TypeError(
                "expected_symbol must be a string."
            )

        expected_symbol = expected_symbol.strip().upper()

        if not expected_symbol:
            raise ValueError(
                "expected_symbol cannot be empty."
            )

        self.expected_symbol = expected_symbol

        if required_fields is None:
            required_fields = (
                self.DEFAULT_REQUIRED_FIELDS
            )

        self.required_fields = tuple(
            required_fields
        )

        if not self.required_fields:
            raise ValueError(
                "required_fields cannot be empty."
            )

        if not isinstance(
            allow_unknown_side,
            bool,
        ):
            raise TypeError(
                "allow_unknown_side must be a boolean."
            )

        if not isinstance(
            allow_missing_order_id,
            bool,
        ):
            raise TypeError(
                "allow_missing_order_id must be a boolean."
            )

        if not isinstance(
            allow_missing_quote_quantity,
            bool,
        ):
            raise TypeError(
                "allow_missing_quote_quantity must be a boolean."
            )

        if not isinstance(
            allow_missing_event_time,
            bool,
        ):
            raise TypeError(
                "allow_missing_event_time must be a boolean."
            )

        if not isinstance(
            enforce_finite_numbers,
            bool,
        ):
            raise TypeError(
                "enforce_finite_numbers must be a boolean."
            )

        if not isinstance(
            enforce_positive_price,
            bool,
        ):
            raise TypeError(
                "enforce_positive_price must be a boolean."
            )

        if not isinstance(
            enforce_positive_quantity,
            bool,
        ):
            raise TypeError(
                "enforce_positive_quantity must be a boolean."
            )

        if not isinstance(
            enforce_non_negative_quote_quantity,
            bool,
        ):
            raise TypeError(
                "enforce_non_negative_quote_quantity "
                "must be a boolean."
            )

        if not isinstance(
            enforce_timestamp_range,
            bool,
        ):
            raise TypeError(
                "enforce_timestamp_range must be a boolean."
            )

        if isinstance(max_future_ms, bool):
            raise TypeError(
                "max_future_ms must be an integer."
            )

        if not isinstance(
            max_future_ms,
            int,
        ):
            raise TypeError(
                "max_future_ms must be an integer."
            )

        if max_future_ms < 0:
            raise ValueError(
                "max_future_ms cannot be negative."
            )

        self.allow_unknown_side = allow_unknown_side
        self.allow_missing_order_id = (
            allow_missing_order_id
        )
        self.allow_missing_quote_quantity = (
            allow_missing_quote_quantity
        )
        self.allow_missing_event_time = (
            allow_missing_event_time
        )
        self.enforce_finite_numbers = (
            enforce_finite_numbers
        )
        self.enforce_positive_price = (
            enforce_positive_price
        )
        self.enforce_positive_quantity = (
            enforce_positive_quantity
        )
        self.enforce_non_negative_quote_quantity = (
            enforce_non_negative_quote_quantity
        )
        self.enforce_timestamp_range = (
            enforce_timestamp_range
        )
        self.max_future_ms = max_future_ms

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        record: Mapping[str, Any],
    ) -> ValidationResult:
        """
        Validate one normalized liquidation record.

        Returns
        -------
        ValidationResult
            Validation result containing all discovered issues.
        """

        issues: list[ValidationIssue] = []

        if not isinstance(record, Mapping):
            return ValidationResult(
                valid=False,
                issues=(
                    ValidationIssue(
                        field="record",
                        message="record must be a mapping.",
                        value=record,
                    ),
                ),
            )

        issues.extend(
            self._validate_required_fields(
                record
            )
        )

        issues.extend(
            self._validate_symbol(
                record
            )
        )

        issues.extend(
            self._validate_side(
                record
            )
        )

        issues.extend(
            self._validate_order_id(
                record
            )
        )

        issues.extend(
            self._validate_price(
                record
            )
        )

        issues.extend(
            self._validate_quantity(
                record
            )
        )

        issues.extend(
            self._validate_quote_quantity(
                record
            )
        )

        issues.extend(
            self._validate_timestamp(
                record,
                field_name="timestamp",
                required=True,
            )
        )

        issues.extend(
            self._validate_timestamp(
                record,
                field_name="event_time",
                required=not self.allow_missing_event_time,
            )
        )

        issues.extend(
            self._validate_timestamp_relationship(
                record
            )
        )

        return ValidationResult(
            valid=not issues,
            issues=tuple(issues),
        )

    def validate_or_raise(
        self,
        record: Mapping[str, Any],
    ) -> None:
        """
        Validate a record and raise ValueError if invalid.
        """

        result = self.validate(record)

        result.raise_if_invalid()

    def validate_many(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> list[ValidationResult]:
        """
        Validate multiple normalized liquidation records.
        """

        if records is None:
            raise ValueError(
                "records cannot be None."
            )

        return [
            self.validate(record)
            for record in records
        ]

    def validate_batch(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        reject_duplicates: bool = True,
    ) -> list[ValidationResult]:
        """
        Validate multiple records and optionally detect duplicates.

        Duplicate issues are added to the corresponding record's
        validation result.
        """

        if records is None:
            raise ValueError(
                "records cannot be None."
            )

        records_list = list(records)

        results = [
            self.validate(record)
            for record in records_list
        ]

        if not reject_duplicates:
            return results

        seen: dict[Any, int] = {}

        mutable_issues = [
            list(result.issues)
            for result in results
        ]

        for index, record in enumerate(records_list):
            if not isinstance(record, Mapping):
                continue

            key = self._record_key(record)

            if key in seen:
                first_index = seen[key]

                mutable_issues[index].append(
                    ValidationIssue(
                        field="record",
                        message=(
                            "duplicate liquidation record; "
                            f"matches record index {first_index}."
                        ),
                        value=key,
                    )
                )
            else:
                seen[key] = index

        return [
            ValidationResult(
                valid=not issues,
                issues=tuple(issues),
            )
            for issues in mutable_issues
        ]

    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------

    def _validate_required_fields(
        self,
        record: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """
        Validate required fields.
        """

        issues: list[ValidationIssue] = []

        for field_name in self.required_fields:
            if field_name not in record:
                issues.append(
                    ValidationIssue(
                        field=field_name,
                        message="required field is missing.",
                    )
                )
                continue

            if record[field_name] is None:
                issues.append(
                    ValidationIssue(
                        field=field_name,
                        message="required field cannot be None.",
                    )
                )

        return issues

    # ------------------------------------------------------------------
    # Symbol
    # ------------------------------------------------------------------

    def _validate_symbol(
        self,
        record: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """
        Validate liquidation symbol.
        """

        issues: list[ValidationIssue] = []

        symbol = record.get("symbol")

        if symbol is None:
            return issues

        if not isinstance(symbol, str):
            issues.append(
                ValidationIssue(
                    field="symbol",
                    message="symbol must be a string.",
                    value=symbol,
                )
            )
            return issues

        normalized = symbol.strip().upper()

        if not normalized:
            issues.append(
                ValidationIssue(
                    field="symbol",
                    message="symbol cannot be empty.",
                    value=symbol,
                )
            )
            return issues

        if normalized != self.expected_symbol:
            issues.append(
                ValidationIssue(
                    field="symbol",
                    message=(
                        "unexpected symbol; expected "
                        f"{self.expected_symbol}."
                    ),
                    value=symbol,
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Side
    # ------------------------------------------------------------------

    def _validate_side(
        self,
        record: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """
        Validate normalized liquidation side.
        """

        issues: list[ValidationIssue] = []

        side = record.get("side")

        if side is None:
            return issues

        if not isinstance(side, str):
            issues.append(
                ValidationIssue(
                    field="side",
                    message="side must be a string.",
                    value=side,
                )
            )
            return issues

        normalized = side.strip().upper()

        if not normalized:
            issues.append(
                ValidationIssue(
                    field="side",
                    message="side cannot be empty.",
                    value=side,
                )
            )
            return issues

        if (
            not self.allow_unknown_side
            and normalized not in self.VALID_SIDES
        ):
            issues.append(
                ValidationIssue(
                    field="side",
                    message=(
                        "side must be BUY or SELL."
                    ),
                    value=side,
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Order ID
    # ------------------------------------------------------------------

    def _validate_order_id(
        self,
        record: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """
        Validate order ID.
        """

        issues: list[ValidationIssue] = []

        order_id = record.get(
            "order_id"
        )

        if order_id is None:
            if not self.allow_missing_order_id:
                issues.append(
                    ValidationIssue(
                        field="order_id",
                        message=(
                            "order_id is required."
                        ),
                    )
                )

            return issues

        if isinstance(order_id, bool):
            issues.append(
                ValidationIssue(
                    field="order_id",
                    message=(
                        "order_id cannot be boolean."
                    ),
                    value=order_id,
                )
            )
            return issues

        if not isinstance(
            order_id,
            (str, int),
        ):
            issues.append(
                ValidationIssue(
                    field="order_id",
                    message=(
                        "order_id must be a string or integer."
                    ),
                    value=order_id,
                )
            )
            return issues

        if isinstance(order_id, str):
            if not order_id.strip():
                issues.append(
                    ValidationIssue(
                        field="order_id",
                        message=(
                            "order_id cannot be empty."
                        ),
                        value=order_id,
                    )
                )

        return issues

    # ------------------------------------------------------------------
    # Price
    # ------------------------------------------------------------------

    def _validate_price(
        self,
        record: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """
        Validate liquidation price.
        """

        issues: list[ValidationIssue] = []

        price = record.get("price")

        if price is None:
            return issues

        if not self._is_real_number(price):
            issues.append(
                ValidationIssue(
                    field="price",
                    message=(
                        "price must be a finite numeric value."
                    ),
                    value=price,
                )
            )
            return issues

        if (
            self.enforce_positive_price
            and price <= 0
        ):
            issues.append(
                ValidationIssue(
                    field="price",
                    message="price must be greater than zero.",
                    value=price,
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Quantity
    # ------------------------------------------------------------------

    def _validate_quantity(
        self,
        record: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """
        Validate liquidation quantity.
        """

        issues: list[ValidationIssue] = []

        quantity = record.get(
            "quantity"
        )

        if quantity is None:
            return issues

        if not self._is_real_number(
            quantity
        ):
            issues.append(
                ValidationIssue(
                    field="quantity",
                    message=(
                        "quantity must be a finite numeric value."
                    ),
                    value=quantity,
                )
            )
            return issues

        if (
            self.enforce_positive_quantity
            and quantity <= 0
        ):
            issues.append(
                ValidationIssue(
                    field="quantity",
                    message=(
                        "quantity must be greater than zero."
                    ),
                    value=quantity,
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Quote quantity
    # ------------------------------------------------------------------

    def _validate_quote_quantity(
        self,
        record: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """
        Validate quote quantity.
        """

        issues: list[ValidationIssue] = []

        value = record.get(
            "quote_quantity"
        )

        if value is None:
            if not self.allow_missing_quote_quantity:
                issues.append(
                    ValidationIssue(
                        field="quote_quantity",
                        message=(
                            "quote_quantity is required."
                        ),
                    )
                )

            return issues

        if not self._is_real_number(value):
            issues.append(
                ValidationIssue(
                    field="quote_quantity",
                    message=(
                        "quote_quantity must be "
                        "a finite numeric value."
                    ),
                    value=value,
                )
            )
            return issues

        if (
            self.enforce_non_negative_quote_quantity
            and value < 0
        ):
            issues.append(
                ValidationIssue(
                    field="quote_quantity",
                    message=(
                        "quote_quantity cannot be negative."
                    ),
                    value=value,
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------

    def _validate_timestamp(
        self,
        record: Mapping[str, Any],
        *,
        field_name: str,
        required: bool,
    ) -> list[ValidationIssue]:
        """
        Validate a timestamp field.
        """

        issues: list[ValidationIssue] = []

        value = record.get(
            field_name
        )

        if value is None:
            if required:
                issues.append(
                    ValidationIssue(
                        field=field_name,
                        message=(
                            "timestamp is required."
                        ),
                    )
                )

            return issues

        if isinstance(value, bool):
            issues.append(
                ValidationIssue(
                    field=field_name,
                    message=(
                        "timestamp must be an integer "
                        "Unix timestamp in milliseconds."
                    ),
                    value=value,
                )
            )
            return issues

        if not isinstance(
            value,
            int,
        ):
            issues.append(
                ValidationIssue(
                    field=field_name,
                    message=(
                        "timestamp must be an integer "
                        "Unix timestamp in milliseconds."
                    ),
                    value=value,
                )
            )
            return issues

        if value < 0:
            issues.append(
                ValidationIssue(
                    field=field_name,
                    message=(
                        "timestamp cannot be negative."
                    ),
                    value=value,
                )
            )
            return issues

        if (
            self.enforce_timestamp_range
            and value
            > self._current_time_ms()
            + self.max_future_ms
        ):
            issues.append(
                ValidationIssue(
                    field=field_name,
                    message=(
                        "timestamp is too far in the future."
                    ),
                    value=value,
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Timestamp relationship
    # ------------------------------------------------------------------

    def _validate_timestamp_relationship(
        self,
        record: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """
        Validate relationship between timestamp and event_time.
        """

        issues: list[ValidationIssue] = []

        timestamp = record.get(
            "timestamp"
        )

        event_time = record.get(
            "event_time"
        )

        if (
            timestamp is None
            or event_time is None
        ):
            return issues

        if not isinstance(timestamp, int):
            return issues

        if not isinstance(event_time, int):
            return issues

        # No strict ordering is imposed because exchange-specific
        # semantics determine which timestamp represents the event
        # versus message/update time.
        #
        # This method intentionally remains conservative.

        return issues

    # ------------------------------------------------------------------
    # Numeric utility
    # ------------------------------------------------------------------

    def _is_real_number(
        self,
        value: Any,
    ) -> bool:
        """
        Check whether a value is a valid numeric value.
        """

        if isinstance(value, bool):
            return False

        if not isinstance(
            value,
            (int, float),
        ):
            return False

        if not self.enforce_finite_numbers:
            return True

        return isfinite(
            float(value)
        )

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------

    @classmethod
    def _record_key(
        cls,
        record: Mapping[str, Any],
    ) -> Any:
        """
        Build a stable identity key for duplicate detection.
        """

        symbol = record.get(
            "symbol"
        )

        order_id = record.get(
            "order_id"
        )

        if order_id is not None:
            return (
                "order",
                symbol,
                str(order_id),
            )

        return (
            "record",
            symbol,
            record.get("side"),
            record.get("timestamp"),
            record.get("price"),
            record.get("quantity"),
            record.get("quote_quantity"),
        )

    # ------------------------------------------------------------------
    # Current time
    # ------------------------------------------------------------------

    @staticmethod
    def _current_time_ms() -> int:
        """
        Return current UTC time in Unix milliseconds.
        """

        return int(
            datetime.now(
                timezone.utc
            ).timestamp()
            * 1000
        )