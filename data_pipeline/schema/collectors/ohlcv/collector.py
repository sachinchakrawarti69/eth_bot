"""
OHLCV Collector Schema

Defines the responsibilities, inputs, outputs, and configuration
for the OHLCV data collector.
"""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class OHLCVCollectorSchema:
    """
    Schema describing the OHLCV collector.
    """

    # ==========================================================
    # Collector Information
    # ==========================================================

    collector_name: str = "ohlcv"

    data_type: str = "market_data"

    source_type: Literal["rest", "websocket"] = "rest"

    # ==========================================================
    # Market Configuration
    # ==========================================================

    symbol: str = "ETHUSDT"

    timeframe: str = "1h"

    market_type: Literal["spot", "futures"] = "futures"

    # ==========================================================
    # Collection Configuration
    # ==========================================================

    historical_supported: bool = True

    realtime_supported: bool = True

    incremental_supported: bool = True

    # ==========================================================
    # Validation
    # ==========================================================

    parser: str = "OHLCVParser"

    validator: str = "OHLCVValidator"

    # ==========================================================
    # Output
    # ==========================================================

    output_schema: str = "RawOHLCVSchema"

    output_format: str = "parquet"

    # ==========================================================
    # Metadata
    # ==========================================================

    version: str = "1.0"

    description: Optional[str] = (
        "Collects OHLCV candles from supported exchanges."
    )