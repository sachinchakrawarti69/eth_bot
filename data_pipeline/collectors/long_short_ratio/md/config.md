# Long/Short Ratio Collector Configuration

## Overview

`config.py` contains the centralized configuration for the **ETH futures long/short ratio collector**.

Its purpose is to keep collection settings separate from the implementation in:

```text
collector.py
```

The configuration controls:

* Symbol.
* Time period.
* API request limit.
* API endpoint.
* Timeout.
* Retry behavior.
* Pagination.
* Historical collection.
* Validation policy.
* Storage behavior.
* Monitoring.

---

# Location

```text
D:\Sachin Chakrawarti\eth_bot\data_pipeline\collectors\long_short_ratio\
│
├── collector.py
├── parser.py
├── validator.py
├── config.py
│
└── md\
    ├── collector.md
    ├── parser.md
    ├── validator.md
    └── config.md
```

---

# Configuration Architecture

```text
LongShortRatioConfig
│
├── collection
│   ├── symbol
│   ├── period
│   ├── limit
│   ├── pagination
│   └── timeout
│
├── api
│   ├── endpoint
│   ├── timeout
│   ├── retries
│   └── rate limit
│
├── historical
│   ├── batch size
│   ├── max pages
│   └── timestamp rules
│
├── validation
│   ├── required fields
│   ├── numeric rules
│   └── symbol rules
│
├── storage
│   ├── dataset name
│   ├── format
│   └── partitioning
│
└── monitoring
    ├── logging
    └── failure alerts
```

---

# Design Principle

The configuration follows:

> **Configuration belongs in `config.py`; behavior belongs in `collector.py`.**

For example:

```text
config.py
    ↓
What should happen?

collector.py
    ↓
How does it happen?
```

This keeps the collector easier to test and modify.

---

# Core Defaults

The module defines the following defaults.

| Setting       |      Default |
| ------------- | -----------: |
| Symbol        |    `ETHUSDT` |
| Period        |         `5m` |
| Limit         |        `500` |
| Minimum limit |          `1` |
| Maximum limit |        `500` |
| Timeout       | `10 seconds` |

---

# Default Symbol

```python
DEFAULT_SYMBOL = "ETHUSDT"
```

The system is specifically focused on ETH futures.

Using a centralized symbol prevents different collector components from accidentally using different instruments.

---

# Default Period

```python
DEFAULT_PERIOD = "5m"
```

The default long/short ratio aggregation period is five minutes.

Other periods can be selected through the configuration.

---

# Supported Periods

The configuration allows:

```text
5m
15m
30m
1h
2h
4h
6h
12h
1d
```

These are stored in:

```python
SUPPORTED_PERIODS
```

as an immutable `frozenset`.

---

# Request Limit

The default limit is:

```text
500
```

The allowed range is:

```text
1 → 500
```

The constants are:

```python
MIN_LIMIT = 1
MAX_LIMIT = 500
```

This prevents invalid API request sizes.

---

# API Configuration

The `LongShortRatioAPIConfig` class contains exchange API settings.

```python
LongShortRatioAPIConfig
```

It contains:

| Setting                          | Purpose                       |
| -------------------------------- | ----------------------------- |
| `endpoint`                       | Long/short ratio API endpoint |
| `timeout_seconds`                | Request timeout               |
| `max_retries`                    | Maximum retry attempts        |
| `retry_backoff_seconds`          | Delay between retries         |
| `rate_limit_requests_per_minute` | Request-rate configuration    |

---

# API Endpoint

The configured endpoint is:

```text
/futures/data/globalLongShortAccountRatio
```

It is kept in configuration rather than hard-coded throughout the collector.

---

# Timeout

Default:

```text
10 seconds
```

Configured through:

```python
timeout_seconds
```

A timeout prevents the data pipeline from waiting indefinitely for an exchange response.

---

# Retry Configuration

Default:

```text
max_retries = 3
```

and:

```text
retry_backoff_seconds = 1.0
```

The retry configuration is intended to work with the base REST infrastructure.

The collector itself should not implement a separate competing retry system.

---

# Rate Limit Configuration

The configuration contains:

```text
rate_limit_requests_per_minute = 120
```

This value represents the intended request-rate policy for the collector.

Actual exchange-specific limits should be verified against the exchange API configuration.

---

# Collection Configuration

The `LongShortRatioCollectionConfig` class controls normal collection behavior.

It includes:

```text
symbol
period
limit
supported_periods
min_limit
max_limit
timeout_seconds
enable_pagination
page_size
stop_on_short_page
stop_on_empty_page
pagination_timestamp_increment
```

---

# Pagination

Pagination is enabled by default:

```text
enable_pagination = True
```

This allows historical data collection to continue across multiple API requests.

---

# Page Size

Default:

```text
page_size = 500
```

This corresponds to the default API limit.

---

# Short Page Behavior

The configuration contains:

```text
stop_on_short_page = True
```

When an API response contains fewer records than requested, pagination can stop because the available range may have been exhausted.

---

# Empty Page Behavior

The configuration contains:

```text
stop_on_empty_page = True
```

An empty API response terminates pagination.

This avoids unnecessary repeated requests.

---

# Pagination Timestamp Increment

The configuration defines:

```text
pagination_timestamp_increment = 1
```

The next request begins after the last returned timestamp.

Conceptually:

```text
next_start_time =
    last_timestamp + 1
```

This helps prevent repeatedly requesting the same observation.

---

# Historical Configuration

Historical collection is controlled by:

```python
LongShortRatioHistoricalConfig
```

It defines:

* Whether historical collection is enabled.
* Historical batch size.
* Maximum number of pages.
* Timestamp ordering requirements.
* Duplicate timestamp policy.

---

# Historical Collection Enabled

Default:

```text
enabled = True
```

This supports the project's historical market-data requirements.

Historical long/short ratio data can contribute to model training datasets.

---

# Historical Batch Size

Default:

```text
500
```

The batch size corresponds to the API's maximum configured page size.

---

# Maximum Pages

Default:

```text
10,000
```

This provides an upper bound for pagination.

It is an important safety mechanism against:

* Infinite loops.
* Unexpected exchange responses.
* Incorrect timestamp progression.
* Misconfigured historical ranges.

---

# Monotonic Timestamps

By default:

```text
require_monotonic_timestamps = True
```

Historical observations are expected to progress forward in time.

Conceptually:

```text
t1 < t2 < t3 < t4
```

rather than:

```text
t1 < t3 < t2
```

---

# Duplicate Timestamps

Default:

```text
allow_duplicate_timestamps = False
```

Duplicate observations should normally be removed or handled before downstream dataset generation.

---

# Validation Configuration

`LongShortRatioValidationConfig` defines the policy for downstream validation.

The actual validation logic belongs in:

```text
validator.py
```

The configuration only defines the rules.

---

# Expected Symbol

Default:

```text
ETHUSDT
```

The validator can use:

```python
expected_symbol
```

to ensure that records belong to the intended ETH futures instrument.

---

# Required Fields

The configuration can require:

```text
symbol
period
timestamp
long_account
short_account
long_short_ratio
```

This ensures that the normalized record contains the fields needed for downstream analysis.

---

# Zero Account Values

The configuration allows:

```text
allow_zero_long_account = True
allow_zero_short_account = True
```

Zero values are not automatically considered invalid because the exchange may legitimately report zero or near-zero account counts in some contexts.

---

# Finite Numbers

The configuration enables:

```text
require_finite_numbers = True
```

This prevents:

```text
NaN
Infinity
-Infinity
```

from entering downstream datasets.

This is particularly important for ML pipelines.

---

# Negative Account Values

The configuration rejects negative account values by default:

```text
reject_negative_accounts = True
```

Negative account counts are not meaningful.

---

# Negative Ratio

The configuration rejects:

```text
long_short_ratio < 0
```

through:

```text
reject_negative_ratio = True
```

---

# Storage Configuration

Storage behavior is defined by:

```python
LongShortRatioStorageConfig
```

It contains:

```text
dataset_name
raw_subdirectory
file_format
partition_by_symbol
partition_by_date
compression
```

---

# Dataset Name

Default:

```text
long_short_ratio
```

This gives the dataset a consistent identity throughout the data pipeline.

---

# Storage Directory

Default raw-data subdirectory:

```text
long_short_ratio
```

This keeps long/short ratio data separate from:

```text
OHLCV
Trades
Order Book
Funding Rate
Open Interest
Liquidations
```

---

# File Format

Default:

```text
parquet
```

Parquet is appropriate for analytical market-data storage because it supports:

* Columnar access.
* Compression.
* Efficient historical queries.
* ML/data-processing workflows.

---

# Compression

Default:

```text
snappy
```

The compression setting is:

```text
compression = "snappy"
```

---

# Partitioning

The configuration enables:

```text
partition_by_symbol = True
partition_by_date = True
```

Conceptually:

```text
long_short_ratio/
│
├── symbol=ETHUSDT/
│   ├── date=2026-08-01/
│   ├── date=2026-08-02/
│   └── date=2026-08-03/
```

The exact physical storage layout depends on the storage implementation.

---

# Monitoring Configuration

Monitoring is defined by:

```python
LongShortRatioMonitoringConfig
```

It controls:

* Request logging.
* Response-size logging.
* Latency logging.
* Empty-response alerts.
* Repeated-failure alerts.

---

# Monitoring Enabled

Default:

```text
enabled = True
```

Monitoring is important for a 24/7 automated data pipeline.

---

# Request Logging

Default:

```text
log_requests = True
```

This can help identify:

* API request failures.
* Incorrect parameters.
* Unexpected collection frequency.
* Operational problems.

Sensitive authentication information must never be logged.

---

# Response Size Logging

Default:

```text
log_response_size = True
```

This can help detect unusual API responses.

For example:

```text
Expected → 500 records
Received → 0 records
```

may indicate an ingestion problem.

---

# Latency Logging

Default:

```text
log_latency = True
```

Monitoring API latency helps identify exchange connectivity problems.

---

# Empty Response Alerts

Default:

```text
alert_on_empty_response = True
```

An empty response can be normal in some historical ranges, so the monitoring layer should interpret the event in context rather than automatically treating every empty response as an exchange failure.

---

# Repeated Failure Alerts

Default:

```text
alert_on_repeated_failure = True
```

The default failure threshold is:

```text
5
```

Repeated failures can indicate:

* API downtime.
* Network problems.
* Authentication problems.
* Rate limiting.
* Incorrect configuration.

---

# Complete Configuration

The top-level configuration is:

```python
LongShortRatioConfig
```

It groups:

```text
collection
api
historical
validation
storage
monitoring
```

This creates one central configuration object.

---

# Default Configuration

The module exposes:

```python
DEFAULT_CONFIG
```

which creates the complete default configuration.

Conceptually:

```text
DEFAULT_CONFIG
│
├── Collection
│   └── ETHUSDT / 5m / 500
│
├── API
│   └── Endpoint / timeout / retry
│
├── Historical
│   └── Pagination controls
│
├── Validation
│   └── Data-quality rules
│
├── Storage
│   └── Parquet / Snappy
│
└── Monitoring
    └── Logging / alerts
```

---

# Configuration Helpers

The module also provides helper functions.

## `normalize_symbol()`

Normalizes symbols to uppercase.

Example:

```python
normalize_symbol(" ethusdt ")
```

returns:

```text
ETHUSDT
```

---

# `normalize_period()`

Normalizes and validates the configured period.

Example:

```python
normalize_period("15M")
```

returns:

```text
15m
```

An unsupported period raises an exception.

---

# `validate_limit()`

Validates that:

```text
1 <= limit <= 500
```

Boolean values are rejected even though Python treats `bool` as a subclass of `int`.

---

# `create_config()`

The recommended helper for constructing a customized configuration is:

```python
create_config()
```

Example:

```python
config = create_config(
    symbol="ETHUSDT",
    period="15m",
    limit=500,
    timeout_seconds=15.0,
    enable_pagination=True,
)
```

The returned object is:

```text
LongShortRatioConfig
```

---

# Immutability

The configuration dataclasses use:

```python
@dataclass(frozen=True, slots=True)
```

This provides two useful properties.

### Frozen

Configuration cannot be accidentally modified after creation.

### Slots

The objects use a compact attribute layout and avoid unnecessary instance dictionaries.

---

# Configuration Flow

The intended flow is:

```text
config.py
    ↓
LongShortRatioConfig
    ↓
collector.py
    ↓
API Request
```

The parser and validator can independently use their relevant configuration sections.

---

# Collector Relationship

The collector should consume settings such as:

```text
symbol
period
limit
timeout
pagination
```

from configuration rather than duplicating constants.

Conceptually:

```text
config.py
    │
    ├── symbol
    ├── period
    ├── limit
    └── pagination
          │
          ↓
collector.py
```

---

# Parser Relationship

The parser should not need to know about:

```text
API retry settings
request timeout
pagination
```

It only needs parser-specific configuration and the raw response.

---

# Validator Relationship

The validator can use:

```text
expected_symbol
required fields
numeric rules
timestamp rules
```

from the validation configuration.

This keeps validation policy independent from collection behavior.

---

# Configuration vs Secrets

API credentials should **not** be hard-coded in this file.

Avoid:

```python
API_KEY = "real-secret-key"
API_SECRET = "real-secret"
```

Instead, secrets should come from the project's secure environment/configuration system.

The configuration module should define behavior, not expose credentials.

---

# Configuration vs Strategy

This file must not contain:

```text
buy conditions
sell conditions
stop-loss rules
take-profit rules
position sizing
risk limits
trade signals
```

Those belong elsewhere in the trading architecture.

---

# Configuration vs Risk Engine

The long/short ratio collector configuration does not determine whether a trade is safe.

The separation remains:

```text
Long/Short Ratio Configuration
        ↓
Data Collection

Risk Configuration
        ↓
Risk Engine
```

These are different concerns.

---

# ML Pipeline Relationship

Long/short ratio data may eventually become a model feature:

```text
Long/Short Ratio
       ↓
Validated Dataset
       ↓
Indicators Analytics
       ↓
Feature Dataset
       ↓
Direction Model
Momentum Model
Trend Model
Volatility Model
```

The configuration module does not contain model configuration.

---

# Testing

Recommended test location:

```text
D:\Sachin Chakrawarti\eth_bot\
tests\
└── collectors\
    └── long_short_ratio\
        └── test_config.py
```

---

# Configuration Tests

Tests should cover:

```text
default configuration
custom configuration
symbol normalization
invalid symbol
period normalization
unsupported period
valid limits
limit below minimum
limit above maximum
negative timeout
zero timeout
invalid timeout type
pagination configuration
validation configuration
storage configuration
monitoring configuration
```

---

# Example

A standard configuration:

```python
config = LongShortRatioConfig()
```

A customized configuration:

```python
config = create_config(
    symbol="ETHUSDT",
    period="15m",
    limit=500,
    timeout_seconds=15.0,
    enable_pagination=True,
)
```

The collector can then use the relevant settings:

```text
config.collection
config.api
config.historical
```

while downstream components use:

```text
config.validation
config.storage
config.monitoring
```

---

# Data Pipeline Position

The configuration sits outside the actual data flow:

```text
                    ┌──────────────┐
                    │   config.py  │
                    └──────┬───────┘
                           │
                           ▼
Exchange → Collector → Parser → Validator → Storage
                                      │
                                      ▼
                               Indicators Analytics
                                      │
                                      ▼
                                Dataset Generator
                                      │
                                      ▼
                                  ML / DL
```

Configuration controls the behavior of the pipeline without becoming part of the market-data records.

---

# Final Responsibility

`long_short_ratio/config.py` has one primary responsibility:

> **Provide centralized, validated, immutable configuration for ETH futures long/short ratio data collection, historical pagination, validation policy, storage, API behavior, and monitoring, while keeping operational settings separate from collection, parsing, analytics, strategy, risk, and execution logic.**
