# Option Chain Collector

## Overview

`option_chain/collector.py` is responsible for collecting raw ETH options-chain market data from the configured exchange API.

It belongs to the **data collection layer** of the ETH Bot data pipeline.

```text
Exchange API
     ↓
Option Chain Collector
     ↓
Raw Response
     ↓
Option Chain Parser
     ↓
Option Chain Validator
     ↓
Processed Storage
     ↓
Indicators Analytics
```

The collector's job is to **acquire data reliably**. It does not interpret, validate, or analyze the returned option-chain records.

---

# Location

```text
D:\Sachin Chakrawarti\eth_bot\data_pipeline\collectors\option_chain\
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

* Connecting to the configured exchange REST API.
* Requesting ETH option-chain information.
* Building request parameters.
* Managing HTTP sessions.
* Applying request timeouts.
* Handling transient HTTP failures.
* Retrying retryable requests.
* Applying exponential backoff.
* Collecting data for one underlying symbol.
* Collecting data for multiple symbols.
* Returning the raw API response.
* Reporting collection failures.

---

# Non-Responsibilities

The collector does **not**:

* Parse individual option records.
* Normalize exchange-specific fields.
* Validate option-chain records.
* Calculate Greeks.
* Calculate implied volatility.
* Calculate option indicators.
* Generate trading signals.
* Generate ML features.
* Decide whether an option trade should be taken.
* Manage trading risk.
* Execute orders.

The separation is:

```text
Collector
    ↓
Acquire raw data

Parser
    ↓
Normalize raw data

Validator
    ↓
Validate normalized data

Analytics
    ↓
Calculate information

Dataset Generator
    ↓
Prepare model data

Models
    ↓
Generate predictions

Strategy
    ↓
Generate trading decisions

Risk Engine
    ↓
Approve/reject trades

Execution Engine
    ↓
Execute orders
```

---

# Main Class

The main class is:

```python
OptionChainCollector
```

It manages communication with the exchange endpoint.

A collector instance contains:

```text
configuration
HTTP session
request logic
retry logic
symbol handling
```

---

# Configuration

The collector uses:

```python
OptionChainCollectorConfig
```

The configuration keeps operational settings separate from collection logic.

Default configuration includes:

```text
base_url
endpoint
symbol
timeout
max_retries
retry_delay
backoff_factor
enabled
verify_ssl
user_agent
```

---

# Default Exchange Endpoint

The default base URL is:

```text
https://eapi.binance.com
```

The configured endpoint is:

```text
/eapi/v1/exchangeInfo
```

The complete URL is constructed by the collector rather than being duplicated throughout the code.

---

# Underlying Symbol

The default underlying symbol is:

```text
ETH
```

The collector normalizes symbols to uppercase.

For example:

```text
"eth"
```

becomes:

```text
ETH
```

and:

```text
" ETH "
```

becomes:

```text
ETH
```

---

# Why the Collector Uses the Underlying Symbol

An option chain represents multiple option contracts belonging to the same underlying asset.

For ETH, the chain can contain contracts with different:

* Expiration dates.
* Strike prices.
* Call/put types.
* Contract identifiers.

Therefore, the collector requests the chain using the underlying:

```text
ETH
```

rather than treating every option contract as a separate API collection task.

---

# HTTP Session

The collector uses:

```python
requests.Session
```

instead of creating a completely independent HTTP connection for every request.

The session provides:

* Connection reuse.
* Shared headers.
* Consistent HTTP configuration.
* Cleaner resource management.

---

# Request Headers

The collector sets:

```text
Accept: application/json
```

and a configured user agent.

The default user agent is:

```text
eth-bot-option-chain-collector/1.0
```

This identifies the application when making requests.

---

# Timeout

The default timeout is:

```text
10 seconds
```

The timeout prevents a request from remaining blocked indefinitely.

The value is configurable through:

```python
timeout
```

Example:

```python
OptionChainCollectorConfig(
    timeout=15.0
)
```

---

# Retry Policy

The collector supports configurable retries.

The default maximum number of attempts is:

```text
3
```

The collector retries transient failures rather than immediately terminating the collection operation.

---

# Retryable HTTP Status Codes

The collector considers these statuses retryable:

```text
408
425
429
500
502
503
504
```

These generally represent temporary request, rate-limit, gateway, or service conditions.

---

# Non-Retryable Errors

Errors that are not considered transient are not repeatedly retried.

For example, a permanent client-side request problem should not cause unnecessary repeated API requests.

The collector stops retrying when the response status is not in the configured retryable set.

---

# Exponential Backoff

Retries use exponential backoff.

The delay is conceptually:

```text
delay = retry_delay × backoff_factor^(attempt - 1)
```

With:

```text
retry_delay = 1
backoff_factor = 2
```

the delays are approximately:

```text
Attempt 1 failure
    ↓
1 second

Attempt 2 failure
    ↓
2 seconds

Attempt 3 failure
    ↓
4 seconds
```

This reduces pressure on the exchange during temporary failures.

---

# Collection Result

The collector returns:

```python
CollectionResult
```

rather than returning only the raw response.

The result contains:

```text
success
data
status_code
error
attempts
```

This makes collection failures observable without forcing every caller to handle exceptions.

---

# Successful Collection

A successful result contains:

```text
success = True
data = raw API response
status_code = HTTP status
attempts = number of attempts
```

The `data` field remains raw.

It is not converted into normalized option records.

---

# Failed Collection

A failed result contains:

```text
success = False
data = None
error = failure description
status_code = HTTP status when available
attempts = number of attempts
```

This allows the scheduler or pipeline controller to decide how to handle the failure.

---

# `collect()`

The main collection method is:

```python
collect()
```

It:

1. Checks whether collection is enabled.
2. Builds request parameters.
3. Sends the HTTP request.
4. Handles retryable failures.
5. Parses the HTTP response as JSON.
6. Returns `CollectionResult`.

Conceptually:

```text
collect()
   ↓
Enabled?
   ↓
Build parameters
   ↓
HTTP GET
   ↓
Successful?
 ┌─┴─┐
Yes  No
 ↓    ↓
JSON  Retry
 ↓    ↓
Result
```

---

# `collect_raw()`

The method:

```python
collect_raw()
```

returns the raw API response directly.

Unlike `collect()`, it raises:

```python
RuntimeError
```

when collection fails.

This is useful when the caller wants failure to immediately interrupt the current pipeline operation.

---

# `collect_for_symbol()`

The method:

```python
collect_for_symbol(symbol)
```

allows collection for a specific underlying symbol.

Example:

```python
collector.collect_for_symbol("ETH")
```

The symbol is normalized before being sent to the API.

---

# `collect_symbols()`

The collector also supports:

```python
collect_symbols(symbols)
```

for multiple underlying symbols.

Conceptually:

```text
["ETH", "BTC", ...]
       ↓
┌──────┼──────┐
↓      ↓      ↓
ETH   BTC    ...
↓      ↓      ↓
Result Result
```

Each symbol is collected independently.

---

# Request Parameters

The request parameters are generated by:

```python
_build_params()
```

The default request contains the configured underlying:

```text
underlying=ETH
```

Keeping parameter construction in a dedicated method makes the collector easier to extend when the exchange API requires additional parameters.

---

# URL Construction

The complete URL is generated by:

```python
_build_url()
```

The method combines:

```text
base_url
+
endpoint
```

For example:

```text
https://eapi.binance.com
```

and:

```text
/eapi/v1/exchangeInfo
```

become:

```text
https://eapi.binance.com/eapi/v1/exchangeInfo
```

---

# JSON Handling

The collector expects a JSON API response.

After a successful HTTP response, it calls:

```python
response.json()
```

The collector does not transform the returned JSON into an internal schema.

That belongs to:

```text
option_chain/parser.py
```

---

# Parser Boundary

The collector should preserve the exchange response as much as possible.

```text
Exchange JSON
      ↓
collector.py
      ↓
raw JSON
      ↓
parser.py
      ↓
normalized OptionChainRecord
```

This prevents exchange-specific assumptions from leaking into the rest of the pipeline.

---

# Validator Boundary

After parsing:

```text
Raw API Response
      ↓
Collector
      ↓
Parser
      ↓
Normalized Records
      ↓
Validator
```

The collector itself should not perform domain validation such as:

```text
valid strike
valid expiration
valid option type
valid bid/ask
valid implied volatility
```

Those checks belong to the validator and downstream data-quality layers.

---

# Exception Handling

The collector handles common `requests` failures:

```text
requests.Timeout
requests.ConnectionError
requests.RequestException
```

A timeout is treated as a transient failure and can be retried.

A connection failure can also be retried.

Other request exceptions terminate the retry loop.

---

# Invalid JSON

If the HTTP request succeeds but the response is not valid JSON, the collector reports the failure.

This prevents invalid API content from being silently passed to the parser.

---

# Collector Enabled Flag

The configuration includes:

```python
enabled
```

By default:

```text
enabled = True
```

When disabled:

```text
collect()
    ↓
success = False
```

No HTTP request is made.

This is useful for selectively disabling an expensive or unnecessary data source without removing its collector from the pipeline.

---

# SSL Verification

The configuration contains:

```python
verify_ssl
```

The default is:

```text
True
```

This keeps TLS certificate verification enabled during normal operation.

---

# Resource Management

The collector provides:

```python
close()
```

to close the HTTP session.

It also supports context-manager usage:

```python
with OptionChainCollector() as collector:
    result = collector.collect()
```

When the context exits, the session is closed.

---

# Configuration Validation

Before collection begins, the collector validates configuration.

It checks:

* Base URL.
* Endpoint.
* Symbol.
* Timeout.
* Retry count.
* Retry delay.
* Backoff factor.
* User-agent type.

Invalid configuration raises an exception during initialization instead of failing later during a live collection request.

---

# Configuration Rules

### Base URL

Must be a non-empty string.

### Endpoint

Must be a non-empty string.

### Symbol

Must be a non-empty string.

### Timeout

Must be greater than zero.

### Maximum retries

Must be at least one.

### Retry delay

Cannot be negative.

### Backoff factor

Must be at least one.

### User agent

Must be a string.

---

# Data Flow

The option-chain collection flow is:

```text
                    ┌───────────────────┐
                    │   Exchange API    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ OptionChain       │
                    │ Collector         │
                    └─────────┬─────────┘
                              │
                    Raw JSON Response
                              │
                              ▼
                    ┌───────────────────┐
                    │ OptionChain       │
                    │ Parser             │
                    └─────────┬─────────┘
                              │
                    Normalized Records
                              │
                              ▼
                    ┌───────────────────┐
                    │ OptionChain       │
                    │ Validator          │
                    └─────────┬─────────┘
                              │
                              ▼
                       Processed Data
```

---

# Relationship With Greeks

Option-chain collection and Greeks calculation should remain separate.

The collector gathers market information such as:

```text
contract
strike
expiry
bid
ask
mark price
volume
open interest
```

The Greeks layer can later calculate:

```text
Delta
Gamma
Theta
Vega
Rho
```

The collector should not perform these calculations.

---

# Relationship With Implied Volatility

Similarly, implied volatility should be calculated downstream.

The flow should be:

```text
Option Chain
     ↓
Parser
     ↓
Validator
     ↓
Processed Option Data
     ↓
Implied Volatility
```

The collector should only acquire the exchange data required for that calculation.

---

# Relationship With ML Dataset Generation

The option-chain collector is upstream of the model-data pipeline.

```text
Option Exchange
      ↓
Option Chain Collector
      ↓
Parser
      ↓
Validator
      ↓
Storage
      ↓
Greeks / IV / Analytics
      ↓
Feature Engineering
      ↓
Dataset Generator
      ↓
Sequence Dataset
      ↓
Attention Dataset
      ↓
ML / DL Model
```

---

# Failure Handling

A typical failure path is:

```text
HTTP Request
     ↓
Timeout
     ↓
Retry
     ↓
Timeout
     ↓
Retry
     ↓
Success
```

If all retries fail:

```text
HTTP Request
     ↓
Failure
     ↓
Retry
     ↓
Failure
     ↓
Retry
     ↓
Failure
     ↓
CollectionResult(success=False)
```

The scheduler or pipeline orchestrator can then decide whether to:

* Retry later.
* Log the failure.
* Mark the data interval incomplete.
* Trigger an alert.
* Continue processing other collectors.

---

# What the Collector Must Preserve

The collector should preserve:

```text
raw exchange structure
raw option contracts
raw exchange metadata
raw timestamps
raw market values
```

until the parser has processed the response.

This is important for reproducibility and debugging.

---

# Raw Data Principle

The collector should follow:

> **Collect first, interpret later.**

This means the collector should avoid prematurely changing:

```text
field names
numeric meanings
option types
expiration formats
strike formats
market-state values
```

The parser owns normalization.

---

# Testing

Recommended test location:

```text
D:\Sachin Chakrawarti\eth_bot\
tests\
└── collectors\
    └── option_chain\
        └── test_collector.py
```

Recommended tests include:

```text
successful request
HTTP timeout
connection failure
retryable HTTP status
non-retryable HTTP status
maximum retry count
exponential backoff
invalid JSON
disabled collector
symbol normalization
empty symbol
invalid timeout
invalid retry configuration
custom base URL
custom endpoint
custom timeout
multiple symbols
session closing
context-manager behavior
```

---

# Mocking HTTP Requests

Tests should not depend on the real exchange API.

The HTTP session should be mocked.

Conceptually:

```text
Test
 ↓
Mock HTTP Session
 ↓
Fake Exchange Response
 ↓
Collector
 ↓
CollectionResult
```

This makes tests:

* Fast.
* Deterministic.
* Offline.
* Reproducible.

---

# Important Design Principle

The collector should not contain trading logic.

It should never contain decisions such as:

```text
BUY
SELL
HOLD
LONG
SHORT
REJECT TRADE
POSITION SIZE
STOP LOSS
TAKE PROFIT
```

Those belong to later components.

---

# Data Quality Principle

The collector is responsible for **transport reliability**, while the validator is responsible for **data quality**.

```text
Collector
    ↓
"Did we successfully retrieve the response?"

Parser
    ↓
"Can we normalize the response?"

Validator
    ↓
"Is the normalized data acceptable?"

Analytics
    ↓
"What can we calculate?"

Strategy
    ↓
"What trade opportunity exists?"

Risk Engine
    ↓
"Can the trade be allowed?"
```

---

# Security and Operational Considerations

The collector should:

* Use HTTPS.
* Keep SSL verification enabled.
* Avoid logging secrets.
* Avoid storing credentials in source code.
* Respect exchange rate limits.
* Use bounded retries.
* Use request timeouts.
* Keep raw API collection separate from trading execution.

If authentication is later required, credentials should be supplied through the configuration/secrets layer rather than hard-coded in `collector.py`.

---

# Future Extension Points

The collector can later be extended with:

```text
rate-limit handling
server-time synchronization
request metrics
latency measurements
structured logging
pagination
historical collection
scheduled collection
response caching
raw-response persistence
API health monitoring
```

These additions should preserve the collector's primary responsibility:

> **Reliable acquisition of raw option-chain market data.**

---

# Recommended Architecture

The option-chain subsystem should follow:

```text
option_chain/
│
├── collector.py
│      │
│      └── Exchange communication
│
├── parser.py
│      │
│      └── Raw response normalization
│
├── validator.py
│      │
│      └── Data-quality validation
│
├── config.py
│      │
│      └── Operational configuration
│
└── md/
       ├── collector.md
       ├── parser.md
       ├── validator.md
       └── config.md
```

---

# Final Responsibility

`option_chain/collector.py` has one core responsibility:

> **Reliably retrieve raw ETH option-chain market data from the configured exchange API, using controlled HTTP requests, timeouts, retries, and error handling, while leaving parsing, validation, analytics, modeling, risk management, and trade execution to their respective downstream components.**
