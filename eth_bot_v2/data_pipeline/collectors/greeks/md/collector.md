# Greeks Collector

## Overview

`greeks/collector.py` is responsible for collecting raw option Greeks data from the configured exchange/API client.

Its responsibility is **data acquisition**.

It does not parse, validate, calculate, analyze, or trade.

```text
Exchange / API
      ↓
collector.py
      ↓
Raw Greeks Response
      ↓
parser.py
      ↓
Normalized Greeks Record
      ↓
validator.py
      ↓
Validated Greeks Data
```

---

# Location

```text
D:\Sachin Chakrawarti\eth_bot\data_pipeline\collectors\greeks\
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

# Primary Responsibility

The collector is responsible for:

* Calling the configured Greeks API client.
* Requesting option Greeks data.
* Passing collection parameters to the API.
* Handling transient request failures.
* Retrying failed requests.
* Applying exponential backoff.
* Adding optional retry jitter.
* Detecting empty API responses.
* Recording collection metadata.
* Returning the raw response to the parser.

---

# Non-Responsibilities

The collector does **not**:

* Parse exchange-specific JSON.
* Normalize field names.
* Validate individual Greeks.
* Calculate Greeks.
* Calculate implied volatility.
* Generate option analytics.
* Generate ML features.
* Generate trading signals.
* Manage positions.
* Approve or reject trades.
* Execute orders.

The separation is:

```text
Collector
    ↓
Acquire

Parser
    ↓
Normalize

Validator
    ↓
Validate
```

---

# Main Class

The primary class is:

```python
GreeksCollector
```

It receives:

```text
API Client
+
GreeksCollectorConfig
```

and produces:

```text
GreeksRawResponse
```

---

# API Client Interface

The collector expects an API client implementing:

```python
get_greeks()
```

with optional parameters:

```text
symbol
expiry
strike
option_type
```

The collector therefore does not depend directly on a particular exchange SDK.

Conceptually:

```text
GreeksCollector
      ↓
GreeksAPIClient
      ↓
Exchange API
```

---

# Dependency Injection

The API client is injected into the collector.

Conceptually:

```python
collector = GreeksCollector(
    client=exchange_client,
    config=config,
)
```

This design makes the collector:

* Testable.
* Exchange-agnostic.
* Easier to replace.
* Easier to mock.
* Less coupled to vendor-specific SDKs.

---

# Configuration

The collector uses:

```python
GreeksCollectorConfig
```

Configuration includes:

```text
symbol
expiry
strike
option_type
timeout_seconds
max_retries
retry_delay_seconds
retry_backoff_factor
jitter_seconds
fail_on_empty_response
```

---

# Symbol

`symbol` identifies the option contract or instrument being requested.

Example:

```text
ETH-26AUG-3500-C
```

The collector normalizes symbols by:

1. Removing surrounding whitespace.
2. Converting to uppercase.
3. Rejecting empty values.

Example:

```text
eth-26aug-3500-c
```

becomes:

```text
ETH-26AUG-3500-C
```

---

# Expiry

The optional:

```text
expiry
```

parameter identifies the requested option expiration.

The collector passes it to the API client.

The collector does not interpret exchange-specific expiry formats.

---

# Strike

The optional:

```text
strike
```

parameter identifies the option strike.

It must be greater than zero when supplied.

The collector does not calculate or validate option pricing.

---

# Option Type

Supported option types are:

```text
CALL
PUT
C
P
```

They are normalized to:

```text
CALL
PUT
```

Examples:

```text
C     → CALL
CALL  → CALL

P     → PUT
PUT   → PUT
```

---

# Timeout

The configuration contains:

```python
timeout_seconds
```

with a default of:

```text
10 seconds
```

This represents the intended request timeout configuration.

The actual enforcement of the timeout depends on the injected API client's implementation.

The collector does not forcibly terminate an arbitrary blocking Python method.

---

# Retry Configuration

The collector supports:

```text
max_retries
retry_delay_seconds
retry_backoff_factor
jitter_seconds
```

Default behavior:

```text
max_retries = 3
retry_delay_seconds = 1.0
retry_backoff_factor = 2.0
jitter_seconds = 0.25
```

Therefore, the maximum number of request attempts is:

```text
max_retries + 1
```

With three retries:

```text
Attempt 1
Attempt 2
Attempt 3
Attempt 4
```

---

# Exponential Backoff

The retry delay follows:

```text
delay =
retry_delay_seconds
×
retry_backoff_factor ^ (attempt - 1)
```

With the default configuration, the base delays are approximately:

```text
Attempt 1 failure → 1 second
Attempt 2 failure → 2 seconds
Attempt 3 failure → 4 seconds
```

Optional jitter is then added.

---

# Retry Jitter

The collector can add a random delay:

```text
0 → jitter_seconds
```

This prevents many collectors from retrying at exactly the same moment.

This is particularly useful when multiple market-data collectors operate concurrently.

---

# Retryable Failures

The collector treats common transient failures such as:

```text
TimeoutError
ConnectionError
OSError
```

as retryable.

Unexpected exceptions are also retried before the collector ultimately fails.

---

# Request Flow

```text
collect()
   ↓
Attempt request
   ↓
API client
   ↓
Response
   │
   ├── Valid response
   │      ↓
   │   Return result
   │
   ├── Empty response
   │      ↓
   │   Response error
   │
   └── Request failure
          ↓
       Retry
          ↓
       Backoff
          ↓
       Next attempt
```

---

# `collect()`

The primary method is:

```python
collect()
```

It:

1. Attempts the API request.
2. Handles failures.
3. Retries when appropriate.
4. Performs minimal response checks.
5. Records collection time.
6. Returns `GreeksRawResponse`.

Example:

```python
result = collector.collect()
```

---

# `collect_data()`

The convenience method:

```python
collect_data()
```

returns only:

```text
raw API payload
```

rather than the complete metadata wrapper.

Example:

```python
raw_data = collector.collect_data()
```

This is useful when the surrounding pipeline already manages metadata.

---

# `collect_many()`

The method:

```python
collect_many(symbols)
```

collects Greeks for multiple option symbols.

Conceptually:

```text
Symbols
   ↓
ETH-...
ETH-...
ETH-...
   ↓
Individual collection
   ↓
GreeksRawResponse[]
```

Each symbol is collected independently.

---

# Raw Response

The collector returns:

```python
GreeksRawResponse
```

This contains:

```text
data
collected_at
symbol
expiry
strike
option_type
attempt
source
```

---

# `data`

The:

```text
data
```

field contains the original API response.

The collector deliberately does not transform the exchange payload.

Example:

```text
data
 ↓
raw exchange response
```

The parser is responsible for interpreting it.

---

# `collected_at`

The collector records:

```text
collected_at
```

as a Unix timestamp in milliseconds.

It represents when the collector received the response.

This is different from a market-data timestamp returned by the exchange.

---

# Collection Timestamp vs Exchange Timestamp

These should not be confused.

```text
Exchange timestamp
    ↓
When the exchange generated the market-data observation

Collection timestamp
    ↓
When our system collected the response
```

The parser/validator can later preserve the exchange timestamp separately.

---

# `attempt`

The response records the successful attempt number.

Example:

```text
attempt = 1
```

means the first request succeeded.

```text
attempt = 3
```

means the collector needed two failed attempts before succeeding.

This is useful for monitoring API reliability.

---

# `source`

The response contains:

```text
source
```

with a default value:

```text
exchange
```

This allows the same collector architecture to distinguish different sources later.

Example:

```text
exchange
backup_exchange
historical_api
test_fixture
```

---

# Empty Responses

The collector performs a minimal check for empty responses.

Examples:

```text
None
[]
{}
""
```

can be considered empty.

If:

```text
fail_on_empty_response = True
```

the collector raises:

```text
GreeksCollectorResponseError
```

---

# Why Empty Responses Matter

A successful HTTP request does not necessarily mean usable market data was received.

For example:

```text
HTTP request
     ↓
200 OK
     ↓
{}
```

is technically a successful request but provides no Greeks data.

The collector therefore detects this condition before passing the response downstream.

---

# Detailed Validation Boundary

The collector only performs **response-level checks**.

It does not validate individual fields such as:

```text
delta
gamma
theta
vega
rho
implied_volatility
```

Those checks belong to:

```text
greeks/validator.py
```

---

# Error Types

The module defines:

```text
GreeksCollectorError
```

as the base exception.

Specialized exceptions include:

```text
GreeksCollectorConfigurationError
GreeksCollectorRequestError
GreeksCollectorResponseError
```

---

# Configuration Error

Configuration problems raise:

```text
GreeksCollectorConfigurationError
```

Examples:

```text
timeout <= 0
max_retries < 0
negative retry delay
backoff factor < 1
negative jitter
invalid option type
invalid strike
empty symbol
```

These are local configuration problems rather than exchange failures.

---

# Request Error

A failed API request ultimately produces:

```text
GreeksCollectorRequestError
```

This indicates that the collector could not successfully acquire the requested data.

---

# Response Error

An unusable API response produces:

```text
GreeksCollectorResponseError
```

For example:

```text
None
{}
[]
```

when empty responses are configured to fail.

---

# Collector Logging

The collector uses Python's:

```python
logging
```

module.

Important events include:

```text
request attempt
retry
retry delay
unexpected request failure
```

Logging is intentionally used instead of `print()`.

---

# Example Logging Flow

```text
DEBUG:
Collecting Greeks data (attempt 1/4)

WARNING:
Transient Greeks collection failure on attempt 1/4

DEBUG:
Waiting 1.173 seconds before Greeks retry

DEBUG:
Collecting Greeks data (attempt 2/4)
```

This provides operational visibility without polluting standard output.

---

# Collector and Parser

The boundary is:

```text
collector.py
     ↓
raw API response
     ↓
parser.py
     ↓
normalized Greeks record
```

The collector should never contain exchange-specific parsing logic.

For example, it should not transform:

```text
deltaValue
```

into:

```text
delta
```

That belongs to the parser.

---

# Collector and Validator

The boundary is:

```text
Collector
    ↓
Raw Response

Parser
    ↓
Normalized Record

Validator
    ↓
Validated Record
```

The collector does not determine whether:

```text
delta > 1
```

is valid.

That is validator responsibility.

---

# Collector and Greeks Calculation

There are two possible data sources:

### Exchange-provided Greeks

```text
Exchange
   ↓
Greeks Collector
   ↓
Raw Greeks
```

### Locally calculated Greeks

```text
Option Market Data
       ↓
Pricing Model
       ↓
Greeks Engine
       ↓
Calculated Greeks
```

The collector only handles the first case.

It does not calculate Greeks locally.

---

# Greek Fields

Downstream normalized records may contain:

```text
delta
gamma
theta
vega
rho
```

and potentially:

```text
implied_volatility
```

The collector does not interpret these fields.

---

# Implied Volatility

Implied volatility should remain conceptually separate.

If the exchange provides IV:

```text
Exchange
   ↓
Collector
   ↓
Parser
   ↓
Validator
```

If IV is calculated locally:

```text
Option Price
     ↓
Pricing Model
     ↓
IV Engine
```

The collector should not calculate IV.

---

# Data Pipeline Position

The Greeks collector belongs to the market-data collection layer:

```text
                    Exchange
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
     OHLCV           Trades          Options
                                         │
                                         ↓
                                    Greeks API
                                         │
                                         ↓
                                  Greeks Collector
                                         │
                                         ↓
                                   Raw Storage
                                         │
                                         ↓
                                     Parser
                                         │
                                         ↓
                                    Validator
```

---

# Raw Storage

The collector's output can be stored in the raw data layer before parsing.

Conceptually:

```text
data_pipeline/
├── raw/
│   └── greeks/
│       └── ...
├── processed/
│   └── greeks/
└── datasets/
```

Raw storage allows the pipeline to reproduce parsing later.

---

# Reproducibility

Keeping the raw response is important because exchange APIs can change their schemas.

If the parser later needs to be updated, previously collected raw responses can be reprocessed without making another exchange request.

Therefore:

```text
Raw Data
    ↓
Immutable source
    ↓
Parser versions can change
    ↓
Processed data can be rebuilt
```

---

# Collection Metadata

A useful raw record conceptually contains:

```text
source
collected_at
request parameters
attempt
raw response
```

This allows later investigation of:

```text
When was the data collected?
From where?
For which option?
How many attempts were needed?
What exactly did the exchange return?
```

---

# Failure Handling

The collector should fail clearly after exhausting retries.

It should not silently return:

```text
None
```

after a failed request.

The surrounding scheduler can then decide whether to:

```text
retry later
log failure
alert monitoring
continue another collector
quarantine the collection cycle
```

---

# Rate Limits

The collector itself does not implement exchange-specific rate-limit rules unless they are added to the API client or configuration layer.

The architecture should preferably keep exchange-specific rate limiting close to the exchange client.

```text
Collector
    ↓
Generic collection logic

API Client
    ↓
Exchange-specific protocol
    ↓
Rate limits
    ↓
Authentication
    ↓
HTTP/WebSocket
```

---

# Scheduler Integration

The collector can be called by a scheduler:

```text
Scheduler
    ↓
Greeks Collector
    ↓
Raw Response
    ↓
Storage
```

The scheduler determines:

* When collection occurs.
* How frequently it occurs.
* Which symbols are collected.
* How failures affect the collection cycle.

The collector should not contain scheduling logic.

---

# Concurrency

If many option contracts need to be collected, concurrency can be implemented at the orchestration layer.

For example:

```text
Scheduler
     ↓
Collection Tasks
     ├── Option A
     ├── Option B
     ├── Option C
     └── Option D
```

The collector remains responsible for one collection operation.

---

# Testing

Recommended test location:

```text
D:\Sachin Chakrawarti\eth_bot\
tests\
└── collectors\
    └── greeks\
        └── test_collector.py
```

Recommended tests include:

```text
successful request
successful request on retry
all retries exhausted
timeout failure
connection failure
unexpected API error
None response
empty list response
empty dictionary response
empty string response
valid response
symbol normalization
option type normalization
invalid option type
invalid strike
invalid timeout
invalid retry count
invalid retry delay
invalid backoff
invalid jitter
collection timestamp
successful attempt number
source metadata
collect_data()
collect_many()
```

---

# Mock API Client

Tests should use a mock client rather than a real exchange.

Conceptually:

```python
class MockGreeksClient:

    def get_greeks(
        self,
        **kwargs,
    ):
        return {
            "symbol": "ETH-26AUG-3500-C",
            "delta": 0.52,
            "gamma": 0.001,
            "theta": -12.5,
            "vega": 18.2,
        }
```

This keeps unit tests:

* Fast.
* Deterministic.
* Independent of network connectivity.
* Independent of exchange availability.

---

# Example Successful Flow

```text
GreeksCollector
       ↓
get_greeks()
       ↓
Exchange response
       ↓
Minimal response check
       ↓
GreeksRawResponse
       ↓
Raw Storage
       ↓
Parser
```

---

# Example Failed Flow

```text
GreeksCollector
       ↓
get_greeks()
       ↓
ConnectionError
       ↓
Retry
       ↓
Backoff
       ↓
get_greeks()
       ↓
ConnectionError
       ↓
Retry
       ↓
Final failure
       ↓
GreeksCollectorRequestError
```

---

# Important Design Principle

The collector follows:

> **Collect first, interpret later.**

Its job is to reliably acquire the exchange response and preserve enough metadata to make the collection traceable.

---

# Final Responsibility

`greeks/collector.py` has one core responsibility:

> **Reliably acquire raw option Greeks data from the configured exchange/API client, handle transient request failures with controlled retries and backoff, perform minimal response-level checks, attach collection metadata, and pass the untouched market-data payload to the parser for normalization.**
