"""
Option Chain Parser

Normalizes raw ETH option-chain API responses into internal records.

Responsibilities:
    - Parse raw exchange responses.
    - Normalize field names.
    - Normalize option type.
    - Normalize timestamps.
    - Convert numeric fields.
    - Produce normalized option-chain records.

This module does not:
    - Make API requests.
    - Validate business/data-quality rules.
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
from typing import Any, Iterable, Mapping, Optional


@dataclass(frozen=True, slots=True)
class OptionChainRecord:
    """
    Normalized option-chain record.
    """

    symbol: str
    option_type: str
    strike_price: float
    expiry_timestamp: int

    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    mark_price: Optional[float] = None

    bid_quantity: Optional[float] = None
    ask_quantity: Optional[float] = None

    volume: Optional[float] = None
    open_interest: Optional[float] = None

    last_price: Optional[float] = None

    underlying_price: Optional[float] = None

    contract_id: Optional[str] = None

    timestamp: Optional[int] = None

    raw: Optional[Mapping[str, Any]] = None


class OptionChainParseError(ValueError):
    """
    Raised when an option-chain response cannot be normalized.
    """


class OptionChainParser:
    """
    Parser for raw option-chain API responses.

    The parser converts exchange-specific structures into
    OptionChainRecord objects.
    """

    OPTION_TYPE_MAP = {
        "C": "CALL",
        "CALL": "CALL",
        "P": "PUT",
        "PUT": "PUT",
    }

    # Common exchange field aliases.
    FIELD_ALIASES = {
        "symbol": (
            "symbol",
            "optionSymbol",
            "option_symbol",
            "contract",
        ),
        "option_type": (
            "option_type",
            "optionType",
            "type",
            "side",
        ),
        "strike_price": (
            "strikePrice",
            "strike_price",
            "strike",
        ),
        "expiry_timestamp": (
            "expiryDate",
            "expiryTimestamp",
            "expiry_timestamp",
            "expiration",
            "expirationTime",
        ),
        "bid_price": (
            "bidPrice",
            "bid_price",
            "bid",
        ),
        "ask_price": (
            "askPrice",
            "ask_price",
            "ask",
        ),
        "mark_price": (
            "markPrice",
            "mark_price",
            "mark",
        ),
        "bid_quantity": (
            "bidQty",
            "bidQuantity",
            "bid_quantity",
        ),
        "ask_quantity": (
            "askQty",
            "askQuantity",
            "ask_quantity",
        ),
        "volume": (
            "volume",
            "vol",
        ),
        "open_interest": (
            "openInterest",
            "open_interest",
            "oi",
        ),
        "last_price": (
            "lastPrice",
            "last_price",
            "last",
        ),
        "underlying_price": (
            "underlyingPrice",
            "underlying_price",
            "underlying",
        ),
        "contract_id": (
            "id",
            "contractId",
            "contract_id",
        ),
        "timestamp": (
            "timestamp",
            "time",
            "updateTime",
            "update_time",
        ),
    }

    def parse(
        self,
        response: Any,
    ) -> list[OptionChainRecord]:
        """
        Parse a raw option-chain API response.

        Supported top-level structures include:

            {
                "optionSymbols": [...]
            }

        or:

            {
                "data": [...]
            }

        or a direct list of option records.
        """

        records = self._extract_records(response)

        parsed: list[OptionChainRecord] = []

        for index, raw_record in enumerate(records):
            try:
                parsed.append(
                    self.parse_record(raw_record)
                )
            except Exception as exc:
                raise OptionChainParseError(
                    f"Failed to parse option-chain "
                    f"record at index {index}: {exc}"
                ) from exc

        return parsed

    def parse_record(
        self,
        raw_record: Mapping[str, Any],
    ) -> OptionChainRecord:
        """
        Parse one raw option-chain record.
        """

        if not isinstance(
            raw_record,
            Mapping,
        ):
            raise OptionChainParseError(
                "Option-chain record must be a mapping."
            )

        symbol = self._parse_symbol(
            self._get_field(
                raw_record,
                "symbol",
                required=True,
            )
        )

        option_type = self._parse_option_type(
            self._get_field(
                raw_record,
                "option_type",
                required=True,
            )
        )

        strike_price = self._parse_float(
            self._get_field(
                raw_record,
                "strike_price",
                required=True,
            ),
            field_name="strike_price",
        )

        expiry_timestamp = self._parse_timestamp(
            self._get_field(
                raw_record,
                "expiry_timestamp",
                required=True,
            ),
            field_name="expiry_timestamp",
        )

        return OptionChainRecord(
            symbol=symbol,
            option_type=option_type,
            strike_price=strike_price,
            expiry_timestamp=expiry_timestamp,
            bid_price=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "bid_price",
                )
            ),
            ask_price=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "ask_price",
                )
            ),
            mark_price=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "mark_price",
                )
            ),
            bid_quantity=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "bid_quantity",
                )
            ),
            ask_quantity=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "ask_quantity",
                )
            ),
            volume=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "volume",
                )
            ),
            open_interest=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "open_interest",
                )
            ),
            last_price=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "last_price",
                )
            ),
            underlying_price=self._parse_optional_float(
                self._get_field(
                    raw_record,
                    "underlying_price",
                )
            ),
            contract_id=self._parse_optional_string(
                self._get_field(
                    raw_record,
                    "contract_id",
                )
            ),
            timestamp=self._parse_optional_timestamp(
                self._get_field(
                    raw_record,
                    "timestamp",
                )
            ),
            raw=dict(raw_record),
        )

    def parse_many(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> list[OptionChainRecord]:
        """
        Parse multiple individual option-chain records.
        """

        parsed: list[OptionChainRecord] = []

        for index, record in enumerate(records):
            try:
                parsed.append(
                    self.parse_record(record)
                )
            except Exception as exc:
                raise OptionChainParseError(
                    f"Failed to parse record at "
                    f"index {index}: {exc}"
                ) from exc

        return parsed

    def parse_expiry(
        self,
        value: Any,
    ) -> int:
        """
        Convert an expiry value to Unix milliseconds.
        """

        return self._parse_timestamp(
            value,
            field_name="expiry_timestamp",
        )

    def parse_timestamp(
        self,
        value: Any,
    ) -> int:
        """
        Convert a timestamp value to Unix milliseconds.
        """

        return self._parse_timestamp(
            value,
            field_name="timestamp",
        )

    # ------------------------------------------------------------------
    # Response Extraction
    # ------------------------------------------------------------------

    def _extract_records(
        self,
        response: Any,
    ) -> list[Mapping[str, Any]]:
        """
        Extract individual option records from common
        API response structures.
        """

        if isinstance(
            response,
            list,
        ):
            return self._ensure_record_mappings(
                response
            )

        if not isinstance(
            response,
            Mapping,
        ):
            raise OptionChainParseError(
                "Response must be a mapping or list."
            )

        candidate_keys = (
            "optionSymbols",
            "option_symbols",
            "options",
            "data",
            "result",
            "contracts",
        )

        for key in candidate_keys:
            value = response.get(key)

            if isinstance(
                value,
                list,
            ):
                return self._ensure_record_mappings(
                    value
                )

        # Some APIs may return a single option object.
        if self._looks_like_option_record(
            response
        ):
            return [response]

        raise OptionChainParseError(
            "Could not find option records in "
            "API response."
        )

    @staticmethod
    def _ensure_record_mappings(
        records: list[Any],
    ) -> list[Mapping[str, Any]]:
        """
        Ensure every extracted record is a mapping.
        """

        result: list[Mapping[str, Any]] = []

        for index, record in enumerate(records):
            if not isinstance(
                record,
                Mapping,
            ):
                raise OptionChainParseError(
                    "Option record at index "
                    f"{index} must be a mapping."
                )

            result.append(record)

        return result

    def _looks_like_option_record(
        self,
        record: Mapping[str, Any],
    ) -> bool:
        """
        Determine whether a mapping resembles one
        normalized/raw option record.
        """

        return (
            self._find_field(
                record,
                "strike_price",
            )
            is not None
            and self._find_field(
                record,
                "expiry_timestamp",
            )
            is not None
        )

    # ------------------------------------------------------------------
    # Field Extraction
    # ------------------------------------------------------------------

    def _get_field(
        self,
        record: Mapping[str, Any],
        field_name: str,
        *,
        required: bool = False,
    ) -> Any:
        """
        Retrieve a field using configured aliases.
        """

        value = self._find_field(
            record,
            field_name,
        )

        if (
            required
            and value is None
        ):
            raise OptionChainParseError(
                f"Required field '{field_name}' "
                "is missing."
            )

        return value

    def _find_field(
        self,
        record: Mapping[str, Any],
        field_name: str,
    ) -> Any:
        """
        Find the first matching field alias.
        """

        aliases = self.FIELD_ALIASES.get(
            field_name,
            (),
        )

        for alias in aliases:
            if alias in record:
                return record[alias]

        return None

    # ------------------------------------------------------------------
    # Symbol
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_symbol(
        value: Any,
    ) -> str:
        """
        Normalize an option symbol.
        """

        if not isinstance(
            value,
            str,
        ):
            raise OptionChainParseError(
                "symbol must be a string."
            )

        symbol = value.strip().upper()

        if not symbol:
            raise OptionChainParseError(
                "symbol cannot be empty."
            )

        return symbol

    # ------------------------------------------------------------------
    # Option Type
    # ------------------------------------------------------------------

    def _parse_option_type(
        self,
        value: Any,
    ) -> str:
        """
        Normalize option type to CALL or PUT.
        """

        if not isinstance(
            value,
            str,
        ):
            raise OptionChainParseError(
                "option_type must be a string."
            )

        normalized = (
            value.strip().upper()
        )

        try:
            return self.OPTION_TYPE_MAP[
                normalized
            ]
        except KeyError as exc:
            raise OptionChainParseError(
                "Unsupported option type: "
                f"{value!r}"
            ) from exc

    # ------------------------------------------------------------------
    # Numeric Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_float(
        value: Any,
        *,
        field_name: str,
    ) -> float:
        """
        Convert a required numeric value to float.
        """

        if value is None:
            raise OptionChainParseError(
                f"{field_name} cannot be None."
            )

        if isinstance(
            value,
            bool,
        ):
            raise OptionChainParseError(
                f"{field_name} cannot be boolean."
            )

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise OptionChainParseError(
                f"{field_name} must be numeric."
            ) from exc

    @classmethod
    def _parse_optional_float(
        cls,
        value: Any,
    ) -> Optional[float]:
        """
        Convert an optional numeric value to float.
        """

        if value is None:
            return None

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            return None

        return cls._parse_float(
            value,
            field_name="numeric field",
        )

    # ------------------------------------------------------------------
    # String Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_optional_string(
        value: Any,
    ) -> Optional[str]:
        """
        Normalize an optional string.
        """

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise OptionChainParseError(
                "String field must be a string."
            )

        value = value.strip()

        return value or None

    # ------------------------------------------------------------------
    # Timestamp Parsing
    # ------------------------------------------------------------------

    @classmethod
    def _parse_timestamp(
        cls,
        value: Any,
        *,
        field_name: str,
    ) -> int:
        """
        Convert a timestamp representation to Unix milliseconds.

        Supported:
            - integer milliseconds
            - numeric strings
            - datetime objects
            - ISO-8601 strings
            - seconds timestamps
            - milliseconds timestamps
        """

        if value is None:
            raise OptionChainParseError(
                f"{field_name} cannot be None."
            )

        if isinstance(
            value,
            bool,
        ):
            raise OptionChainParseError(
                f"{field_name} cannot be boolean."
            )

        if isinstance(
            value,
            datetime,
        ):
            return cls._datetime_to_milliseconds(
                value
            )

        if isinstance(
            value,
            (int, float),
        ):
            return cls._numeric_timestamp_to_ms(
                value,
                field_name=field_name,
            )

        if isinstance(
            value,
            str,
        ):
            value = value.strip()

            if not value:
                raise OptionChainParseError(
                    f"{field_name} cannot be empty."
                )

            # Numeric timestamp string.
            try:
                numeric_value = float(value)

                return cls._numeric_timestamp_to_ms(
                    numeric_value,
                    field_name=field_name,
                )
            except ValueError:
                pass

            # ISO-8601 timestamp.
            try:
                parsed_datetime = (
                    datetime.fromisoformat(
                        value.replace(
                            "Z",
                            "+00:00",
                        )
                    )
                )

                return cls._datetime_to_milliseconds(
                    parsed_datetime
                )

            except ValueError as exc:
                raise OptionChainParseError(
                    f"Invalid {field_name}: "
                    f"{value!r}"
                ) from exc

        raise OptionChainParseError(
            f"Unsupported {field_name} type: "
            f"{type(value).__name__}"
        )

    @classmethod
    def _parse_optional_timestamp(
        cls,
        value: Any,
    ) -> Optional[int]:
        """
        Parse an optional timestamp.
        """

        if value is None:
            return None

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            return None

        return cls._parse_timestamp(
            value,
            field_name="timestamp",
        )

    @staticmethod
    def _numeric_timestamp_to_ms(
        value: float,
        *,
        field_name: str,
    ) -> int:
        """
        Convert numeric seconds or milliseconds
        into Unix milliseconds.
        """

        if value <= 0:
            raise OptionChainParseError(
                f"{field_name} must be positive."
            )

        # Unix timestamps below 1e11 are treated as seconds.
        if value < 100_000_000_000:
            value *= 1000

        return int(value)

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


# ----------------------------------------------------------------------
# Convenience Functions
# ----------------------------------------------------------------------

def parse_option_chain(
    response: Any,
) -> list[OptionChainRecord]:
    """
    Parse a raw option-chain API response.
    """

    return OptionChainParser().parse(
        response
    )


def parse_option_chain_record(
    record: Mapping[str, Any],
) -> OptionChainRecord:
    """
    Parse one raw option-chain record.
    """

    return OptionChainParser().parse_record(
        record
    )


def parse_option_chain_records(
    records: Iterable[Mapping[str, Any]],
) -> list[OptionChainRecord]:
    """
    Parse multiple raw option-chain records.
    """

    return OptionChainParser().parse_many(
        records
    )