"""
Open Interest Validator

Validates normalized open-interest records produced by
OpenInterestParser.

Responsibilities:
    - Validate required fields.
    - Validate data types.
    - Validate timestamp values.
    - Validate symbol values.
    - Validate open-interest values.
    - Validate optional open-interest notional values.
    - Detect duplicate timestamps.
    - Validate chronological ordering.

This module does not:
    - Make API requests.
    - Parse exchange-specific responses.
    - Store data.
    - Calculate trading signals.
    - Calculate ML features.
    - Execute trades.
"""

from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


class OpenInterestValidationError(ValueError):
    """
    Raised when an open-interest record fails validation.
    """


class OpenInterestValidator:
    """
    Validator for normalized open-interest records.
    """

    validator_name = "open_interest"
    validator_version = "1.0"

    REQUIRED_FIELDS = (
        "timestamp",
        "symbol",
        "open_interest",
    )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        record: Mapping[str, Any],
    ) -> bool:
        """
        Validate a single normalized record.

        Returns
        -------
        bool
            True when the record is valid.

        Raises
        ------
        OpenInterestValidationError
            If validation fails.
        """

        errors = self.validate_record(record)

        if errors:
            raise OpenInterestValidationError(
                "; ".join(errors)
            )

        return True

    def validate_record(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Return validation errors for a single record.

        An empty list means the record is valid.
        """

        errors: List[str] = []

        if not isinstance(record, Mapping):
            return [
                "record must be a mapping."
            ]

        errors.extend(
            self._validate_required_fields(record)
        )

        errors.extend(
            self._validate_timestamp(record)
        )

        errors.extend(
            self._validate_datetime(record)
        )

        errors.extend(
            self._validate_symbol(record)
        )

        errors.extend(
            self._validate_open_interest(record)
        )

        errors.extend(
            self._validate_open_interest_value(record)
        )

        return errors

    def validate_records(
        self,
        records: Sequence[Mapping[str, Any]],
        *,
        require_chronological_order: bool = False,
        reject_duplicates: bool = True,
    ) -> bool:
        """
        Validate a collection of normalized records.

        Parameters
        ----------
        records:
            Normalized open-interest records.

        require_chronological_order:
            Require timestamps to be non-decreasing.

        reject_duplicates:
            Reject duplicate timestamps for the same symbol.

        Returns
        -------
        bool
            True when all records are valid.

        Raises
        ------
        OpenInterestValidationError
            If any record fails validation.
        """

        errors = self.collect_errors(
            records,
            require_chronological_order=(
                require_chronological_order
            ),
            reject_duplicates=reject_duplicates,
        )

        if errors:
            raise OpenInterestValidationError(
                "; ".join(errors)
            )

        return True

    def collect_errors(
        self,
        records: Sequence[Mapping[str, Any]],
        *,
        require_chronological_order: bool = False,
        reject_duplicates: bool = True,
    ) -> List[str]:
        """
        Validate a collection and return all errors.

        Unlike validate_records(), this method does not raise.
        """

        errors: List[str] = []

        if not isinstance(records, Sequence):
            return [
                "records must be a sequence."
            ]

        timestamps_seen: set[tuple[str, int]] = set()
        previous_timestamp: Optional[int] = None

        for index, record in enumerate(records):
            record_errors = self.validate_record(
                record
            )

            for error in record_errors:
                errors.append(
                    f"record[{index}]: {error}"
                )

            if not isinstance(record, Mapping):
                continue

            timestamp = record.get("timestamp")
            symbol = record.get("symbol")

            if (
                isinstance(timestamp, int)
                and not isinstance(timestamp, bool)
                and isinstance(symbol, str)
            ):
                duplicate_key = (
                    symbol,
                    timestamp,
                )

                if (
                    reject_duplicates
                    and duplicate_key in timestamps_seen
                ):
                    errors.append(
                        f"record[{index}]: duplicate "
                        f"timestamp for symbol "
                        f"{symbol}: {timestamp}."
                    )

                timestamps_seen.add(
                    duplicate_key
                )

                if (
                    require_chronological_order
                    and previous_timestamp is not None
                    and timestamp < previous_timestamp
                ):
                    errors.append(
                        f"record[{index}]: timestamp "
                        f"is not in chronological order."
                    )

                previous_timestamp = timestamp

        return errors

    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------

    def _validate_required_fields(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate presence of required fields.
        """

        errors: List[str] = []

        for field in self.REQUIRED_FIELDS:
            if field not in record:
                errors.append(
                    f"missing required field '{field}'."
                )
                continue

            if record[field] is None:
                errors.append(
                    f"required field '{field}' cannot be None."
                )

        return errors

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------

    def _validate_timestamp(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate normalized Unix-millisecond timestamp.
        """

        if "timestamp" not in record:
            return []

        value = record["timestamp"]

        if isinstance(value, bool):
            return [
                "timestamp must be an integer."
            ]

        if not isinstance(value, int):
            return [
                "timestamp must be an integer in "
                "Unix milliseconds."
            ]

        if value < 0:
            return [
                "timestamp cannot be negative."
            ]

        # Basic sanity check:
        # 2000-01-01 through far-future dates are supported.
        if value < 946684800000:
            return [
                "timestamp is earlier than 2000-01-01."
            ]

        if value > 4102444800000:
            return [
                "timestamp is later than 2100-01-01."
            ]

        return []

    # ------------------------------------------------------------------
    # Datetime
    # ------------------------------------------------------------------

    def _validate_datetime(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate optional datetime representation.
        """

        if "datetime" not in record:
            return []

        value = record["datetime"]

        if value is None:
            return []

        if not isinstance(value, datetime):
            return [
                "datetime must be a datetime instance."
            ]

        if value.tzinfo is None:
            return [
                "datetime must be timezone-aware."
            ]

        return []

    # ------------------------------------------------------------------
    # Symbol
    # ------------------------------------------------------------------

    def _validate_symbol(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate trading symbol.
        """

        if "symbol" not in record:
            return []

        value = record["symbol"]

        if not isinstance(value, str):
            return [
                "symbol must be a string."
            ]

        if not value.strip():
            return [
                "symbol cannot be empty."
            ]

        return []

    # ------------------------------------------------------------------
    # Open interest
    # ------------------------------------------------------------------

    def _validate_open_interest(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate open-interest quantity.
        """

        if "open_interest" not in record:
            return []

        value = record["open_interest"]

        errors = self._validate_numeric(
            value,
            field="open_interest",
        )

        if errors:
            return errors

        if value < 0:
            return [
                "open_interest cannot be negative."
            ]

        return []

    # ------------------------------------------------------------------
    # Open interest value
    # ------------------------------------------------------------------

    def _validate_open_interest_value(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate optional open-interest notional/value.
        """

        if "open_interest_value" not in record:
            return []

        value = record["open_interest_value"]

        errors = self._validate_numeric(
            value,
            field="open_interest_value",
        )

        if errors:
            return errors

        if value < 0:
            return [
                "open_interest_value cannot be negative."
            ]

        return []

    # ------------------------------------------------------------------
    # Numeric validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_numeric(
        value: Any,
        *,
        field: str,
    ) -> List[str]:
        """
        Validate a numeric field.
        """

        if isinstance(value, bool):
            return [
                f"{field} must be numeric."
            ]

        if not isinstance(
            value,
            (int, float),
        ):
            return [
                f"{field} must be numeric."
            ]

        if isinstance(value, float) and not isfinite(value):
            return [
                f"{field} must be finite."
            ]

        return []