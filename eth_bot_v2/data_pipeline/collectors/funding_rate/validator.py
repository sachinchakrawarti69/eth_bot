"""
Funding Rate Validator

Validates standardized funding-rate records before they enter
the storage layer or downstream feature pipeline.

Responsibilities:
    - Validate required fields.
    - Validate symbol.
    - Validate funding-rate values.
    - Validate timestamps.
    - Validate optional mark price.
    - Detect duplicate timestamps within a batch.
    - Detect invalid timestamp ordering when requested.
    - Return validation results.

This module does not:
    - Collect exchange data.
    - Parse raw exchange responses.
    - Store data.
    - Calculate features.
    - Generate trading signals.
    - Approve or reject trades.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class FundingRateValidator:
    """
    Validator for standardized funding-rate records.
    """

    validator_name = "funding_rate"
    validator_version = "1.0"

    REQUIRED_FIELDS = (
        "symbol",
        "funding_rate",
        "funding_time",
    )

    DEFAULT_SYMBOL = "ETHUSDT"

    # Funding rates are normally small. This is a structural
    # safety boundary, not a trading-signal threshold.
    DEFAULT_MIN_FUNDING_RATE = -1.0
    DEFAULT_MAX_FUNDING_RATE = 1.0

    def __init__(
        self,
        *,
        expected_symbol: Optional[str] = DEFAULT_SYMBOL,
        min_funding_rate: float = DEFAULT_MIN_FUNDING_RATE,
        max_funding_rate: float = DEFAULT_MAX_FUNDING_RATE,
        require_mark_price: bool = False,
        enforce_timestamp_order: bool = True,
        reject_duplicates: bool = True,
    ) -> None:
        """
        Initialize the funding-rate validator.
        """

        self.expected_symbol = (
            expected_symbol.strip()
            if expected_symbol is not None
            else None
        )

        self.min_funding_rate = float(
            min_funding_rate
        )

        self.max_funding_rate = float(
            max_funding_rate
        )

        self.require_mark_price = (
            require_mark_price
        )

        self.enforce_timestamp_order = (
            enforce_timestamp_order
        )

        self.reject_duplicates = (
            reject_duplicates
        )

        self._validate_configuration()

    def validate(
        self,
        record: Mapping[str, Any],
    ) -> bool:
        """
        Validate one funding-rate record.

        Returns
        -------
        bool
            True when the record passes validation.

        Raises
        ------
        ValueError
            When validation fails.
        """

        errors = self.validate_record(record)

        if errors:
            raise ValueError(
                "; ".join(errors)
            )

        return True

    def validate_record(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate one funding-rate record and return all errors.
        """

        errors: List[str] = []

        if not isinstance(record, Mapping):
            return [
                "Funding-rate record must be a mapping."
            ]

        errors.extend(
            self._validate_required_fields(record)
        )

        if errors:
            return errors

        errors.extend(
            self._validate_symbol(record)
        )

        errors.extend(
            self._validate_funding_rate(record)
        )

        errors.extend(
            self._validate_funding_time(record)
        )

        errors.extend(
            self._validate_mark_price(record)
        )

        return errors

    def validate_batch(
        self,
        records: Sequence[Mapping[str, Any]],
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a batch of funding-rate records.

        Returns
        -------
        tuple
            (
                batch_is_valid,
                validation_results
            )
        """

        results: List[Dict[str, Any]] = []
        timestamps: List[int] = []

        for index, record in enumerate(records):
            errors = self.validate_record(record)

            timestamp = None

            if isinstance(record, Mapping):
                timestamp = record.get(
                    "funding_time"
                )

            if not errors and timestamp is not None:
                timestamps.append(
                    int(timestamp)
                )

            results.append(
                {
                    "index": index,
                    "valid": not errors,
                    "errors": errors,
                }
            )

        if self.reject_duplicates:
            duplicate_indexes = (
                self._find_duplicate_indexes(
                    timestamps,
                    records,
                )
            )

            for index in duplicate_indexes:
                results[index]["valid"] = False
                results[index]["errors"].append(
                    "Duplicate funding timestamp."
                )

        if self.enforce_timestamp_order:
            ordering_errors = (
                self._find_timestamp_order_errors(
                    records
                )
            )

            for index, message in ordering_errors:
                results[index]["valid"] = False
                results[index]["errors"].append(
                    message
                )

        batch_valid = all(
            result["valid"]
            for result in results
        )

        return batch_valid, results

    def filter_valid(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Return only records that pass validation.
        """

        valid_records: List[Dict[str, Any]] = []

        for record in records:
            if not self.validate_record(record):
                valid_records.append(
                    dict(record)
                )

        return valid_records

    def validate_or_none(
        self,
        record: Mapping[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Return the record when valid, otherwise None.
        """

        errors = self.validate_record(record)

        if errors:
            return None

        return dict(record)

    def _validate_configuration(self) -> None:
        """
        Validate validator configuration.
        """

        if (
            self.expected_symbol is not None
            and not self.expected_symbol
        ):
            raise ValueError(
                "expected_symbol cannot be empty."
            )

        if not math.isfinite(
            self.min_funding_rate
        ):
            raise ValueError(
                "min_funding_rate must be finite."
            )

        if not math.isfinite(
            self.max_funding_rate
        ):
            raise ValueError(
                "max_funding_rate must be finite."
            )

        if (
            self.min_funding_rate
            > self.max_funding_rate
        ):
            raise ValueError(
                "min_funding_rate cannot exceed "
                "max_funding_rate."
            )

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
                    f"Missing required field: {field}."
                )
                continue

            if record[field] is None:
                errors.append(
                    f"Required field cannot be None: {field}."
                )

        return errors

    def _validate_symbol(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate the funding-rate symbol.
        """

        errors: List[str] = []

        symbol = record.get("symbol")

        if not isinstance(symbol, str):
            errors.append(
                "symbol must be a string."
            )
            return errors

        symbol = symbol.strip()

        if not symbol:
            errors.append(
                "symbol cannot be empty."
            )
            return errors

        if (
            self.expected_symbol is not None
            and symbol != self.expected_symbol
        ):
            errors.append(
                "Unexpected symbol: "
                f"{symbol!r}; expected "
                f"{self.expected_symbol!r}."
            )

        return errors

    def _validate_funding_rate(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate funding-rate numeric value.
        """

        errors: List[str] = []

        value = record.get("funding_rate")

        if isinstance(value, bool):
            errors.append(
                "funding_rate cannot be boolean."
            )
            return errors

        if not isinstance(
            value,
            (int, float),
        ):
            errors.append(
                "funding_rate must be numeric."
            )
            return errors

        value = float(value)

        if not math.isfinite(value):
            errors.append(
                "funding_rate must be finite."
            )
            return errors

        if value < self.min_funding_rate:
            errors.append(
                "funding_rate is below the allowed "
                f"minimum of {self.min_funding_rate}."
            )

        if value > self.max_funding_rate:
            errors.append(
                "funding_rate is above the allowed "
                f"maximum of {self.max_funding_rate}."
            )

        return errors

    def _validate_funding_time(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate funding timestamp.
        """

        errors: List[str] = []

        value = record.get("funding_time")

        if isinstance(value, bool):
            errors.append(
                "funding_time cannot be boolean."
            )
            return errors

        if isinstance(value, datetime):
            timestamp = self._datetime_to_milliseconds(
                value
            )
        elif isinstance(value, (int, float)):
            timestamp = value
        else:
            errors.append(
                "funding_time must be a Unix timestamp "
                "in milliseconds."
            )
            return errors

        if not math.isfinite(float(timestamp)):
            errors.append(
                "funding_time must be finite."
            )
            return errors

        if float(timestamp) < 0:
            errors.append(
                "funding_time cannot be negative."
            )

        return errors

    def _validate_mark_price(
        self,
        record: Mapping[str, Any],
    ) -> List[str]:
        """
        Validate optional mark price.
        """

        errors: List[str] = []

        if (
            self.require_mark_price
            and record.get("mark_price") is None
        ):
            errors.append(
                "mark_price is required."
            )
            return errors

        value = record.get("mark_price")

        if value is None:
            return errors

        if isinstance(value, bool):
            errors.append(
                "mark_price cannot be boolean."
            )
            return errors

        if not isinstance(
            value,
            (int, float),
        ):
            errors.append(
                "mark_price must be numeric."
            )
            return errors

        value = float(value)

        if not math.isfinite(value):
            errors.append(
                "mark_price must be finite."
            )
            return errors

        if value <= 0:
            errors.append(
                "mark_price must be greater than zero."
            )

        return errors

    def _find_duplicate_indexes(
        self,
        timestamps: Sequence[int],
        records: Sequence[Mapping[str, Any]],
    ) -> List[int]:
        """
        Find indexes containing duplicate symbol/timestamp pairs.
        """

        seen = set()
        duplicate_indexes: List[int] = []

        for index, record in enumerate(records):
            if not isinstance(record, Mapping):
                continue

            timestamp = record.get(
                "funding_time"
            )

            symbol = record.get(
                "symbol"
            )

            if timestamp is None:
                continue

            key = (
                symbol,
                int(timestamp),
            )

            if key in seen:
                duplicate_indexes.append(index)
            else:
                seen.add(key)

        return duplicate_indexes

    def _find_timestamp_order_errors(
        self,
        records: Sequence[Mapping[str, Any]],
    ) -> List[Tuple[int, str]]:
        """
        Detect records whose funding timestamps move backwards.

        Funding records are expected to be chronological when
        supplied as a batch.
        """

        errors: List[Tuple[int, str]] = []

        previous_timestamp: Optional[int] = None

        for index, record in enumerate(records):
            if not isinstance(record, Mapping):
                continue

            timestamp = record.get(
                "funding_time"
            )

            if timestamp is None:
                continue

            try:
                current_timestamp = int(
                    timestamp
                )
            except (TypeError, ValueError):
                continue

            if (
                previous_timestamp is not None
                and current_timestamp
                < previous_timestamp
            ):
                errors.append(
                    (
                        index,
                        "funding_time is earlier than "
                        "the previous record.",
                    )
                )

            previous_timestamp = current_timestamp

        return errors

    @staticmethod
    def _datetime_to_milliseconds(
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