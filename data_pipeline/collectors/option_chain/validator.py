"""
Option Chain Validator

Validates normalized ETH option-chain records.

Responsibilities:
    - Validate normalized option-chain records.
    - Validate required fields.
    - Validate option type.
    - Validate numeric values.
    - Validate prices and quantities.
    - Validate timestamps.
    - Validate basic market-data consistency.

This module does not:
    - Make API requests.
    - Parse raw API responses.
    - Calculate Greeks.
    - Calculate implied volatility.
    - Generate indicators.
    - Generate ML features.
    - Generate trading signals.
    - Perform risk management.
    - Execute trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Iterable, Optional

from .parser import OptionChainRecord


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Result of option-chain validation.
    """

    valid: bool
    errors: tuple[str, ...] = ()


class OptionChainValidationError(ValueError):
    """
    Raised when an option-chain record fails validation.
    """


class OptionChainValidator:
    """
    Validates normalized OptionChainRecord objects.

    Validation is intentionally limited to data quality and
    structural consistency. Trading decisions are outside
    the responsibility of this class.
    """

    VALID_OPTION_TYPES = frozenset(
        {
            "CALL",
            "PUT",
        }
    )

    MIN_TIMESTAMP_MS = 946684800000  # 2000-01-01
    MAX_TIMESTAMP_MS = 4102444800000  # 2100-01-01

    def validate(
        self,
        record: OptionChainRecord,
    ) -> ValidationResult:
        """
        Validate one option-chain record.

        Returns:
            ValidationResult
        """

        errors: list[str] = []

        errors.extend(
            self._validate_symbol(record)
        )

        errors.extend(
            self._validate_option_type(record)
        )

        errors.extend(
            self._validate_strike_price(record)
        )

        errors.extend(
            self._validate_expiry(record)
        )

        errors.extend(
            self._validate_price_fields(record)
        )

        errors.extend(
            self._validate_quantity_fields(record)
        )

        errors.extend(
            self._validate_market_fields(record)
        )

        errors.extend(
            self._validate_timestamp(record)
        )

        errors.extend(
            self._validate_temporal_relationships(
                record
            )
        )

        return ValidationResult(
            valid=not errors,
            errors=tuple(errors),
        )

    def validate_or_raise(
        self,
        record: OptionChainRecord,
    ) -> None:
        """
        Validate a record and raise if invalid.
        """

        result = self.validate(record)

        if not result.valid:
            raise OptionChainValidationError(
                "; ".join(result.errors)
            )

    def is_valid(
        self,
        record: OptionChainRecord,
    ) -> bool:
        """
        Return True when the record passes validation.
        """

        return self.validate(record).valid

    def validate_many(
        self,
        records: Iterable[OptionChainRecord],
    ) -> list[ValidationResult]:
        """
        Validate multiple option-chain records.
        """

        return [
            self.validate(record)
            for record in records
        ]

    def filter_valid(
        self,
        records: Iterable[OptionChainRecord],
    ) -> list[OptionChainRecord]:
        """
        Return only records that pass validation.
        """

        return [
            record
            for record in records
            if self.is_valid(record)
        ]

    def filter_invalid(
        self,
        records: Iterable[OptionChainRecord],
    ) -> list[OptionChainRecord]:
        """
        Return only records that fail validation.
        """

        return [
            record
            for record in records
            if not self.is_valid(record)
        ]

    # ------------------------------------------------------------------
    # Symbol
    # ------------------------------------------------------------------

    def _validate_symbol(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate option symbol.
        """

        errors: list[str] = []

        if not isinstance(
            record.symbol,
            str,
        ):
            errors.append(
                "symbol must be a string"
            )
            return errors

        if not record.symbol.strip():
            errors.append(
                "symbol cannot be empty"
            )

        if record.symbol != record.symbol.strip():
            errors.append(
                "symbol cannot contain "
                "leading or trailing whitespace"
            )

        if record.symbol != record.symbol.upper():
            errors.append(
                "symbol must be uppercase"
            )

        return errors

    # ------------------------------------------------------------------
    # Option Type
    # ------------------------------------------------------------------

    def _validate_option_type(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate normalized option type.
        """

        if (
            record.option_type
            not in self.VALID_OPTION_TYPES
        ):
            return [
                "option_type must be CALL or PUT"
            ]

        return []

    # ------------------------------------------------------------------
    # Strike
    # ------------------------------------------------------------------

    def _validate_strike_price(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate strike price.
        """

        errors = self._validate_positive_finite(
            record.strike_price,
            "strike_price",
        )

        return errors

    # ------------------------------------------------------------------
    # Expiry
    # ------------------------------------------------------------------

    def _validate_expiry(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate expiration timestamp.
        """

        errors: list[str] = []

        if not self._is_integer(
            record.expiry_timestamp
        ):
            errors.append(
                "expiry_timestamp must be an integer"
            )
            return errors

        if not (
            self.MIN_TIMESTAMP_MS
            <= record.expiry_timestamp
            <= self.MAX_TIMESTAMP_MS
        ):
            errors.append(
                "expiry_timestamp is outside "
                "the supported timestamp range"
            )

        return errors

    # ------------------------------------------------------------------
    # Prices
    # ------------------------------------------------------------------

    def _validate_price_fields(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate option price fields.
        """

        errors: list[str] = []

        price_fields = (
            "bid_price",
            "ask_price",
            "mark_price",
            "last_price",
            "underlying_price",
        )

        for field_name in price_fields:
            value = getattr(
                record,
                field_name,
            )

            errors.extend(
                self._validate_optional_non_negative(
                    value,
                    field_name,
                )
            )

        return errors

    # ------------------------------------------------------------------
    # Quantities
    # ------------------------------------------------------------------

    def _validate_quantity_fields(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate quantity-related fields.
        """

        errors: list[str] = []

        quantity_fields = (
            "bid_quantity",
            "ask_quantity",
            "volume",
            "open_interest",
        )

        for field_name in quantity_fields:
            value = getattr(
                record,
                field_name,
            )

            errors.extend(
                self._validate_optional_non_negative(
                    value,
                    field_name,
                )
            )

        return errors

    # ------------------------------------------------------------------
    # Market Consistency
    # ------------------------------------------------------------------

    def _validate_market_fields(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate relationships between market fields.
        """

        errors: list[str] = []

        if (
            record.bid_price is not None
            and record.ask_price is not None
            and record.bid_price > record.ask_price
        ):
            errors.append(
                "bid_price cannot be greater "
                "than ask_price"
            )

        if (
            record.mark_price is not None
            and record.bid_price is not None
            and record.ask_price is not None
            and not (
                record.bid_price
                <= record.mark_price
                <= record.ask_price
            )
        ):
            errors.append(
                "mark_price should be between "
                "bid_price and ask_price"
            )

        return errors

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------

    def _validate_timestamp(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate optional market-data timestamp.
        """

        if record.timestamp is None:
            return []

        if not self._is_integer(
            record.timestamp
        ):
            return [
                "timestamp must be an integer"
            ]

        if not (
            self.MIN_TIMESTAMP_MS
            <= record.timestamp
            <= self.MAX_TIMESTAMP_MS
        ):
            return [
                "timestamp is outside "
                "the supported timestamp range"
            ]

        return []

    # ------------------------------------------------------------------
    # Temporal Relationships
    # ------------------------------------------------------------------

    def _validate_temporal_relationships(
        self,
        record: OptionChainRecord,
    ) -> list[str]:
        """
        Validate basic timestamp relationships.
        """

        errors: list[str] = []

        if (
            record.timestamp is not None
            and record.expiry_timestamp
            < record.timestamp
        ):
            errors.append(
                "expiry_timestamp cannot be earlier "
                "than record timestamp"
            )

        return errors

    # ------------------------------------------------------------------
    # Generic Numeric Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_positive_finite(
        value: object,
        field_name: str,
    ) -> list[str]:
        """
        Validate a required positive finite number.
        """

        errors: list[str] = []

        if isinstance(
            value,
            bool,
        ):
            errors.append(
                f"{field_name} cannot be boolean"
            )
            return errors

        if not isinstance(
            value,
            (int, float),
        ):
            errors.append(
                f"{field_name} must be numeric"
            )
            return errors

        if not isfinite(float(value)):
            errors.append(
                f"{field_name} must be finite"
            )
            return errors

        if value <= 0:
            errors.append(
                f"{field_name} must be greater than zero"
            )

        return errors

    @staticmethod
    def _validate_optional_non_negative(
        value: Optional[float],
        field_name: str,
    ) -> list[str]:
        """
        Validate an optional non-negative finite number.
        """

        if value is None:
            return []

        errors: list[str] = []

        if isinstance(
            value,
            bool,
        ):
            errors.append(
                f"{field_name} cannot be boolean"
            )
            return errors

        if not isinstance(
            value,
            (int, float),
        ):
            errors.append(
                f"{field_name} must be numeric"
            )
            return errors

        if not isfinite(float(value)):
            errors.append(
                f"{field_name} must be finite"
            )
            return errors

        if value < 0:
            errors.append(
                f"{field_name} cannot be negative"
            )

        return errors

    # ------------------------------------------------------------------
    # Type Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_integer(
        value: object,
    ) -> bool:
        """
        Check whether a value is an integer
        without accepting booleans.
        """

        return (
            isinstance(value, int)
            and not isinstance(value, bool)
        )


# ----------------------------------------------------------------------
# Convenience Functions
# ----------------------------------------------------------------------

def validate_option_chain(
    record: OptionChainRecord,
) -> ValidationResult:
    """
    Validate one option-chain record.
    """

    return OptionChainValidator().validate(
        record
    )


def validate_option_chain_or_raise(
    record: OptionChainRecord,
) -> None:
    """
    Validate one option-chain record and raise
    OptionChainValidationError when invalid.
    """

    OptionChainValidator().validate_or_raise(
        record
    )


def is_valid_option_chain(
    record: OptionChainRecord,
) -> bool:
    """
    Return True when the option-chain record is valid.
    """

    return OptionChainValidator().is_valid(
        record
    )


def filter_valid_option_chain_records(
    records: Iterable[OptionChainRecord],
) -> list[OptionChainRecord]:
    """
    Return only valid option-chain records.
    """

    return OptionChainValidator().filter_valid(
        records
    )