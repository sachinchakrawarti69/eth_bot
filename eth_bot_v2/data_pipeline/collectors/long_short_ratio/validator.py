"""
Long/Short Ratio Validator

Validates normalized ETH futures long/short ratio records before they
enter processed storage or downstream analytics.

Responsibilities:
    - Validate required fields.
    - Validate field types.
    - Validate symbol and period.
    - Validate timestamps.
    - Validate numeric values.
    - Validate ratio consistency.
    - Detect duplicate timestamps.
    - Detect non-monotonic timestamps.
    - Validate batches of records.
    - Produce validation errors without modifying source records.

This module does not:
    - Collect exchange data.
    - Parse exchange responses.
    - Calculate trading indicators.
    - Generate features.
    - Generate trading signals.
    - Approve or reject trades.
    - Manage portfolio risk.
    - Execute orders.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Optional

from .parser import LongShortRatioRecord


@dataclass(frozen=True, slots=True)
class ValidationError:
    """
    Represents one validation failure.
    """

    field: str
    message: str
    index: Optional[int] = None

    def __str__(self) -> str:
        if self.index is None:
            return f"{self.field}: {self.message}"

        return (
            f"record[{self.index}]."
            f"{self.field}: {self.message}"
        )


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Result of validating one record or a collection of records.
    """

    valid: bool
    errors: tuple[ValidationError, ...] = ()

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def raise_if_invalid(self) -> None:
        """
        Raise ValueError when validation failed.
        """

        if not self.valid:
            message = "; ".join(
                str(error)
                for error in self.errors
            )

            raise ValueError(
                f"Long/short ratio validation failed: "
                f"{message}"
            )


@dataclass(frozen=True, slots=True)
class BatchValidationResult:
    """
    Validation result for multiple records.
    """

    valid: bool
    total_records: int
    valid_records: int
    invalid_records: int
    errors: tuple[ValidationError, ...] = ()

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def validation_rate(self) -> float:
        """
        Return percentage of valid records.
        """

        if self.total_records == 0:
            return 0.0

        return (
            self.valid_records
            / self.total_records
            * 100.0
        )


@dataclass(frozen=True, slots=True)
class LongShortRatioValidationConfig:
    """
    Validation policy for normalized long/short ratio records.
    """

    expected_symbol: str = "ETHUSDT"

    supported_periods: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "5m",
                "15m",
                "30m",
                "1h",
                "2h",
                "4h",
                "6h",
                "12h",
                "1d",
            }
        )
    )

    require_symbol: bool = True
    require_period: bool = True
    require_timestamp: bool = True
    require_long_account: bool = True
    require_short_account: bool = True
    require_long_short_ratio: bool = True

    allow_zero_long_account: bool = True
    allow_zero_short_account: bool = True

    reject_negative_accounts: bool = True
    reject_negative_ratio: bool = True

    require_finite_numbers: bool = True

    require_positive_timestamp: bool = True

    validate_ratio_consistency: bool = True

    ratio_tolerance: float = 1e-9

    allow_duplicate_timestamps: bool = False

    require_monotonic_timestamps: bool = True

    max_future_timestamp_ms: int = 86_400_000


class LongShortRatioValidator:
    """
    Validator for normalized long/short ratio records.

    The validator operates only on normalized records produced by
    LongShortRatioParser.
    """

    def __init__(
        self,
        config: Optional[
            LongShortRatioValidationConfig
        ] = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else LongShortRatioValidationConfig()
        )

        self._validate_configuration()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        record: LongShortRatioRecord,
    ) -> ValidationResult:
        """
        Validate one normalized record.
        """

        errors: list[ValidationError] = []

        if not isinstance(
            record,
            LongShortRatioRecord,
        ):
            errors.append(
                ValidationError(
                    field="record",
                    message=(
                        "expected LongShortRatioRecord, "
                        f"got {type(record).__name__}"
                    ),
                )
            )

            return ValidationResult(
                valid=False,
                errors=tuple(errors),
            )

        errors.extend(
            self._validate_symbol(record)
        )

        errors.extend(
            self._validate_period(record)
        )

        errors.extend(
            self._validate_timestamp(record)
        )

        errors.extend(
            self._validate_long_account(record)
        )

        errors.extend(
            self._validate_short_account(record)
        )

        errors.extend(
            self._validate_ratio(record)
        )

        if self.config.validate_ratio_consistency:
            errors.extend(
                self._validate_ratio_consistency(
                    record
                )
            )

        return ValidationResult(
            valid=not errors,
            errors=tuple(errors),
        )

    def validate_many(
        self,
        records: Iterable[
            LongShortRatioRecord
        ],
    ) -> BatchValidationResult:
        """
        Validate multiple normalized records.

        The input iterable is materialized once so that duplicate and
        timestamp-order checks can be performed consistently.
        """

        materialized = list(records)

        errors: list[ValidationError] = []

        valid_records = 0
        invalid_records = 0

        for index, record in enumerate(
            materialized
        ):
            result = self.validate(
                record
            )

            if result.valid:
                valid_records += 1
            else:
                invalid_records += 1

            errors.extend(
                ValidationError(
                    field=error.field,
                    message=error.message,
                    index=index,
                )
                for error in result.errors
            )

        errors.extend(
            self._validate_batch_structure(
                materialized
            )
        )

        return BatchValidationResult(
            valid=not errors,
            total_records=len(
                materialized
            ),
            valid_records=valid_records,
            invalid_records=invalid_records,
            errors=tuple(errors),
        )

    def is_valid(
        self,
        record: LongShortRatioRecord,
    ) -> bool:
        """
        Return True when one record passes validation.
        """

        return self.validate(record).valid

    def is_batch_valid(
        self,
        records: Iterable[
            LongShortRatioRecord
        ],
    ) -> bool:
        """
        Return True when all records pass validation.
        """

        return self.validate_many(
            records
        ).valid

    def filter_valid(
        self,
        records: Iterable[
            LongShortRatioRecord
        ],
    ) -> list[LongShortRatioRecord]:
        """
        Return only valid records.

        The original records are not modified.
        """

        valid: list[
            LongShortRatioRecord
        ] = []

        for record in records:
            if self.is_valid(record):
                valid.append(record)

        return valid

    def filter_invalid(
        self,
        records: Iterable[
            LongShortRatioRecord
        ],
    ) -> list[LongShortRatioRecord]:
        """
        Return only invalid records.
        """

        invalid: list[
            LongShortRatioRecord
        ] = []

        for record in records:
            if not self.is_valid(record):
                invalid.append(record)

        return invalid

    # ------------------------------------------------------------------
    # Symbol validation
    # ------------------------------------------------------------------

    def _validate_symbol(
        self,
        record: LongShortRatioRecord,
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        symbol = record.symbol

        if self.config.require_symbol:
            if not isinstance(
                symbol,
                str,
            ):
                errors.append(
                    ValidationError(
                        field="symbol",
                        message="must be a string",
                    )
                )

            elif not symbol.strip():
                errors.append(
                    ValidationError(
                        field="symbol",
                        message="cannot be empty",
                    )
                )

        if (
            isinstance(symbol, str)
            and symbol.strip()
        ):
            normalized = symbol.strip().upper()

            if normalized != symbol:
                errors.append(
                    ValidationError(
                        field="symbol",
                        message=(
                            "must be normalized to "
                            "uppercase without surrounding "
                            "whitespace"
                        ),
                    )
                )

            if (
                self.config.expected_symbol
                and normalized
                != self.config.expected_symbol.upper()
            ):
                errors.append(
                    ValidationError(
                        field="symbol",
                        message=(
                            "unexpected symbol "
                            f"'{symbol}', expected "
                            f"'{self.config.expected_symbol}'"
                        ),
                    )
                )

        return errors

    # ------------------------------------------------------------------
    # Period validation
    # ------------------------------------------------------------------

    def _validate_period(
        self,
        record: LongShortRatioRecord,
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        period = record.period

        if self.config.require_period:
            if not isinstance(
                period,
                str,
            ):
                errors.append(
                    ValidationError(
                        field="period",
                        message="must be a string",
                    )
                )

            elif not period.strip():
                errors.append(
                    ValidationError(
                        field="period",
                        message="cannot be empty",
                    )
                )

        if isinstance(
            period,
            str,
        ):
            normalized = period.strip().lower()

            if normalized != period:
                errors.append(
                    ValidationError(
                        field="period",
                        message=(
                            "must be normalized to "
                            "lowercase without surrounding "
                            "whitespace"
                        ),
                    )
                )

            if (
                normalized
                and normalized
                not in self.config.supported_periods
            ):
                errors.append(
                    ValidationError(
                        field="period",
                        message=(
                            f"unsupported period '{period}'"
                        ),
                    )
                )

        return errors

    # ------------------------------------------------------------------
    # Timestamp validation
    # ------------------------------------------------------------------

    def _validate_timestamp(
        self,
        record: LongShortRatioRecord,
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        timestamp = record.timestamp

        if self.config.require_timestamp:
            if not isinstance(
                timestamp,
                int,
            ) or isinstance(
                timestamp,
                bool,
            ):
                errors.append(
                    ValidationError(
                        field="timestamp",
                        message=(
                            "must be an integer "
                            "Unix timestamp in milliseconds"
                        ),
                    )
                )

                return errors

            if timestamp <= 0:
                errors.append(
                    ValidationError(
                        field="timestamp",
                        message=(
                            "must be greater than zero"
                        ),
                    )
                )

            return errors

        if timestamp is not None:
            if not isinstance(
                timestamp,
                int,
            ) or isinstance(
                timestamp,
                bool,
            ):
                errors.append(
                    ValidationError(
                        field="timestamp",
                        message=(
                            "must be an integer"
                        ),
                    )
                )

        return errors

    # ------------------------------------------------------------------
    # Long account validation
    # ------------------------------------------------------------------

    def _validate_long_account(
        self,
        record: LongShortRatioRecord,
    ) -> list[ValidationError]:
        return self._validate_account_value(
            value=record.long_account,
            field_name="long_account",
            allow_zero=(
                self.config.allow_zero_long_account
            ),
        )

    # ------------------------------------------------------------------
    # Short account validation
    # ------------------------------------------------------------------

    def _validate_short_account(
        self,
        record: LongShortRatioRecord,
    ) -> list[ValidationError]:
        return self._validate_account_value(
            value=record.short_account,
            field_name="short_account",
            allow_zero=(
                self.config.allow_zero_short_account
            ),
        )

    def _validate_account_value(
        self,
        *,
        value: Any,
        field_name: str,
        allow_zero: bool,
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        if not isinstance(
            value,
            (int, float),
        ) or isinstance(
            value,
            bool,
        ):
            errors.append(
                ValidationError(
                    field=field_name,
                    message="must be numeric",
                )
            )

            return errors

        numeric = float(value)

        if self.config.require_finite_numbers:
            if not isfinite(numeric):
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=(
                            "must be finite"
                        ),
                    )
                )

        if (
            self.config.reject_negative_accounts
            and numeric < 0
        ):
            errors.append(
                ValidationError(
                    field=field_name,
                    message=(
                        "cannot be negative"
                    ),
                )
            )

        if (
            not allow_zero
            and numeric == 0
        ):
            errors.append(
                ValidationError(
                    field=field_name,
                    message=(
                        "cannot be zero"
                    ),
                )
            )

        return errors

    # ------------------------------------------------------------------
    # Ratio validation
    # ------------------------------------------------------------------

    def _validate_ratio(
        self,
        record: LongShortRatioRecord,
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        value = record.long_short_ratio

        if not isinstance(
            value,
            (int, float),
        ) or isinstance(
            value,
            bool,
        ):
            errors.append(
                ValidationError(
                    field="long_short_ratio",
                    message="must be numeric",
                )
            )

            return errors

        numeric = float(value)

        if self.config.require_finite_numbers:
            if not isfinite(numeric):
                errors.append(
                    ValidationError(
                        field="long_short_ratio",
                        message="must be finite",
                    )
                )

        if (
            self.config.reject_negative_ratio
            and numeric < 0
        ):
            errors.append(
                ValidationError(
                    field="long_short_ratio",
                    message="cannot be negative",
                )
            )

        return errors

    # ------------------------------------------------------------------
    # Ratio consistency
    # ------------------------------------------------------------------

    def _validate_ratio_consistency(
        self,
        record: LongShortRatioRecord,
    ) -> list[ValidationError]:
        """
        Check whether the ratio is mathematically consistent with
        long_account / short_account when such a calculation is valid.

        This check is intentionally tolerant because exchange-side
        calculations may use different rounding rules.
        """

        errors: list[ValidationError] = []

        long_account = record.long_account
        short_account = record.short_account
        ratio = record.long_short_ratio

        if not self._is_finite_number(
            long_account
        ):
            return errors

        if not self._is_finite_number(
            short_account
        ):
            return errors

        if not self._is_finite_number(
            ratio
        ):
            return errors

        if short_account == 0:
            return errors

        expected_ratio = (
            long_account
            / short_account
        )

        tolerance = (
            self.config.ratio_tolerance
        )

        if not self._approximately_equal(
            ratio,
            expected_ratio,
            tolerance,
        ):
            errors.append(
                ValidationError(
                    field="long_short_ratio",
                    message=(
                        "is inconsistent with "
                        "long_account / short_account "
                        f"(expected approximately "
                        f"{expected_ratio}, received "
                        f"{ratio})"
                    ),
                )
            )

        return errors

    # ------------------------------------------------------------------
    # Batch validation
    # ------------------------------------------------------------------

    def _validate_batch_structure(
        self,
        records: Sequence[
            LongShortRatioRecord
        ],
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        if not records:
            return errors

        if not self.config.allow_duplicate_timestamps:
            errors.extend(
                self._find_duplicate_timestamps(
                    records
                )
            )

        if self.config.require_monotonic_timestamps:
            errors.extend(
                self._find_non_monotonic_timestamps(
                    records
                )
            )

        return errors

    def _find_duplicate_timestamps(
        self,
        records: Sequence[
            LongShortRatioRecord
        ],
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        seen: dict[int, int] = {}

        for index, record in enumerate(
            records
        ):
            if not isinstance(
                record,
                LongShortRatioRecord,
            ):
                continue

            timestamp = record.timestamp

            if not isinstance(
                timestamp,
                int,
            ):
                continue

            if timestamp in seen:
                errors.append(
                    ValidationError(
                        field="timestamp",
                        message=(
                            "duplicate timestamp; "
                            f"first occurrence is "
                            f"record[{seen[timestamp]}]"
                        ),
                        index=index,
                    )
                )
            else:
                seen[timestamp] = index

        return errors

    def _find_non_monotonic_timestamps(
        self,
        records: Sequence[
            LongShortRatioRecord
        ],
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        previous_timestamp: Optional[int] = None

        for index, record in enumerate(
            records
        ):
            if not isinstance(
                record,
                LongShortRatioRecord,
            ):
                continue

            timestamp = record.timestamp

            if not isinstance(
                timestamp,
                int,
            ):
                continue

            if (
                previous_timestamp is not None
                and timestamp
                < previous_timestamp
            ):
                errors.append(
                    ValidationError(
                        field="timestamp",
                        message=(
                            "timestamps must be "
                            "monotonically increasing; "
                            f"received {timestamp} after "
                            f"{previous_timestamp}"
                        ),
                        index=index,
                    )
                )

            previous_timestamp = timestamp

        return errors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_finite_number(
        value: Any,
    ) -> bool:
        if not isinstance(
            value,
            (int, float),
        ) or isinstance(
            value,
            bool,
        ):
            return False

        return isfinite(
            float(value)
        )

    @staticmethod
    def _approximately_equal(
        first: float,
        second: float,
        tolerance: float,
    ) -> bool:
        return abs(
            first - second
        ) <= tolerance

    # ------------------------------------------------------------------
    # Configuration validation
    # ------------------------------------------------------------------

    def _validate_configuration(
        self,
    ) -> None:
        config = self.config

        if not isinstance(
            config.expected_symbol,
            str,
        ):
            raise TypeError(
                "expected_symbol must be a string."
            )

        if not config.expected_symbol.strip():
            raise ValueError(
                "expected_symbol cannot be empty."
            )

        if not config.supported_periods:
            raise ValueError(
                "supported_periods cannot be empty."
            )

        if config.ratio_tolerance < 0:
            raise ValueError(
                "ratio_tolerance cannot be negative."
            )

        if config.max_future_timestamp_ms < 0:
            raise ValueError(
                "max_future_timestamp_ms cannot be negative."
            )


# ============================================================================
# Convenience Functions
# ============================================================================

def validate_record(
    record: LongShortRatioRecord,
    *,
    config: Optional[
        LongShortRatioValidationConfig
    ] = None,
) -> ValidationResult:
    """
    Convenience function for validating one record.
    """

    validator = LongShortRatioValidator(
        config=config
    )

    return validator.validate(
        record
    )


def validate_records(
    records: Iterable[
        LongShortRatioRecord
    ],
    *,
    config: Optional[
        LongShortRatioValidationConfig
    ] = None,
) -> BatchValidationResult:
    """
    Convenience function for validating multiple records.
    """

    validator = LongShortRatioValidator(
        config=config
    )

    return validator.validate_many(
        records
    )


def is_valid_record(
    record: LongShortRatioRecord,
    *,
    config: Optional[
        LongShortRatioValidationConfig
    ] = None,
) -> bool:
    """
    Convenience boolean validator.
    """

    return validate_record(
        record,
        config=config,
    ).valid