"""
OHLCV Collector Configuration Schema

Defines the configuration structure for the OHLCV collector.
"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional


@dataclass
class OHLCVCollectorConfig:
    """
    Configuration schema for the OHLCV collector.
    """

    # ==========================================================
    # Exchange
    # ==========================================================

    exchange: str = "binance"

    market_type: Literal["spot", "futures"] = "futures"

    # ==========================================================
    # Market
    # ==========================================================

    symbol: str = "ETHUSDT"

    timeframe: str = "1h"

    # ==========================================================
    # Collection Mode
    # ==========================================================

    mode: Literal[
        "historical",
        "live",
        "incremental",
    ] = "historical"

    # ==========================================================
    # Historical Collection
    # ==========================================================

    start_time: Optional[str] = None

    end_time: Optional[str] = None

    limit: int = 1000

    # ==========================================================
    # Live Collection
    # ==========================================================

    websocket_enabled: bool = True

    polling_interval: int = 60

    # ==========================================================
    # Retry
    # ==========================================================

    max_retries: int = 5

    retry_delay: float = 2.0

    exponential_backoff: bool = True

    # ==========================================================
    # Network
    # ==========================================================

    timeout: int = 30

    rate_limit_per_second: int = 10

    # ==========================================================
    # Storage
    # ==========================================================

    output_format: Literal[
        "parquet",
        "csv",
        "json",
    ] = "parquet"

    compression: str = "snappy"

    # ==========================================================
    # Validation
    # ==========================================================

    validate_data: bool = True

    remove_duplicates: bool = True

    fill_missing: bool = False

    # ==========================================================
    # Logging
    # ==========================================================

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
    ] = "INFO"

    # ==========================================================
    # Metadata
    # ==========================================================

    version: str = "1.0"

    tags: List[str] = field(default_factory=list)