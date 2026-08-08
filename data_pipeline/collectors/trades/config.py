"""
Trades Collector Runtime Configuration

Configuration for collecting trade-level market data
for the ETH futures data pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional


@dataclass
class TradesCollectorConfig:
    """
    Runtime configuration for the Trades Collector.
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

    # ==========================================================
    # Collection
    # ==========================================================

    historical_enabled: bool = True

    live_enabled: bool = True

    incremental_enabled: bool = True

    # ==========================================================
    # Historical Collection
    # ==========================================================

    start_time: Optional[str] = None

    end_time: Optional[str] = None

    limit: int = 1000

    # ==========================================================
    # WebSocket
    # ==========================================================

    websocket_enabled: bool = True

    reconnect_enabled: bool = True

    reconnect_delay: float = 2.0

    max_reconnect_attempts: int = 10

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
    # Data Handling
    # ==========================================================

    preserve_raw_response: bool = True

    batch_size: int = 1000

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