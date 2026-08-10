"""
Order Book Collector Runtime Configuration

Runtime configuration for collecting ETH futures order-book
snapshots and live depth updates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class OrderBookCollectorConfig:
    """
    Runtime configuration for the Order Book Collector.
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
    # Snapshot Collection
    # ==========================================================

    snapshot_enabled: bool = True

    depth_limit: int = 100

    snapshot_interval: Optional[float] = None

    # ==========================================================
    # Live Collection
    # ==========================================================

    live_enabled: bool = True

    websocket_enabled: bool = True

    # ==========================================================
    # WebSocket Reconnection
    # ==========================================================

    reconnect_enabled: bool = True

    reconnect_delay: float = 2.0

    max_reconnect_attempts: int = 10

    # ==========================================================
    # REST Retry
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
    # Order Book Synchronization
    # ==========================================================

    require_snapshot_before_updates: bool = True

    validate_update_sequence: bool = True

    preserve_update_id: bool = True

    # ==========================================================
    # Raw Data
    # ==========================================================

    preserve_raw_response: bool = True

    batch_size: int = 100

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