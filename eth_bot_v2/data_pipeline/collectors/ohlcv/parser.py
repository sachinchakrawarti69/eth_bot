"""
OHLCV Parser Schema

Defines the parsing contract for transforming raw exchange
responses into the standardized RawOHLCVSchema.

This module defines the parser structure only.
Actual parsing logic belongs to the runtime collector.
"""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class OHLCVParserSchema:
    """
    Schema describing the OHLCV parser.
    """

    # ==========================================================
    # Parser Information
    # ==========================================================

    parser_name: str = "ohlcv_parser"

    parser_version: str = "1.0"

    description: str = (
        "Parses raw OHLCV exchange responses into "
        "RawOHLCVSchema."
    )

    # ==========================================================
    # Input
    # ==========================================================

    input_source: Literal[
        "REST_API",
        "WEBSOCKET"
    ] = "REST_API"

    input_format: Literal[
        "JSON",
        "LIST",
        "ARRAY"
    ] = "JSON"

    # ==========================================================
    # Output
    # ==========================================================

    output_schema: str = "RawOHLCVSchema"

    output_format: Literal[
        "OBJECT",
        "LIST"
    ] = "OBJECT"

    # ==========================================================
    # Parsing Options
    # ==========================================================

    normalize_timestamp: bool = True

    normalize_symbol: bool = True

    normalize_timeframe: bool = True

    convert_numeric_types: bool = True

    preserve_raw_data: bool = False

    # ==========================================================
    # Error Handling
    # ==========================================================

    skip_invalid_records: bool = True

    allow_partial_records: bool = False

    # ==========================================================
    # Metadata
    # ==========================================================

    author: Optional[str] = None

    notes: Optional[str] = None