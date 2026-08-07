"""
OHLCV Validator Schema

Defines the validation contract for standardized OHLCV
records before they are written to raw storage.

This module contains the validator schema only.
Validation logic belongs to the runtime implementation.
"""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class OHLCVValidatorSchema:
    """
    Schema describing the OHLCV validator.
    """

    # ==========================================================
    # Validator Information
    # ==========================================================

    validator_name: str = "ohlcv_validator"

    validator_version: str = "1.0"

    description: str = (
        "Validates standardized OHLCV records prior "
        "to persistence."
    )

    # ==========================================================
    # Input / Output
    # ==========================================================

    input_schema: str = "RawOHLCVSchema"

    output_schema: str = "RawOHLCVSchema"

    # ==========================================================
    # Validation Rules
    # ==========================================================

    validate_required_fields: bool = True

    validate_timestamp: bool = True

    validate_symbol: bool = True

    validate_timeframe: bool = True

    validate_price_values: bool = True

    validate_volume: bool = True

    validate_data_types: bool = True

    validate_duplicates: bool = True

    validate_chronological_order: bool = True

    # ==========================================================
    # Error Policy
    # ==========================================================

    on_validation_error: Literal[
        "REJECT",
        "SKIP",
        "LOG"
    ] = "REJECT"

    allow_partial_records: bool = False

    # ==========================================================
    # Metadata
    # ==========================================================

    author: Optional[str] = None

    notes: Optional[str] = None