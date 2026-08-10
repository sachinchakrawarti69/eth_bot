# Option Chain Collector Configuration

## Overview

`option_chain/config.py` contains the configuration model used by the ETH option-chain collector.

Its purpose is to keep **operational configuration separate from collection logic**.

```text
config.py
    ↓
OptionChainCollector
    ↓
Exchange API
```

The configuration controls:

* Exchange endpoint.
* Underlying symbol.
* HTTP timeout.
* SSL verification.
* User agent.
* Retry policy.
* Backoff behavior.
* Retryable HTTP status codes.
* Collector enable/disable state.

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

# Main Configuration Class

The primary configuration class is:

```python
OptionChainConfig
```

It is implemented as a frozen, slotted dataclass.

Conceptually:

```text
OptionChainConfig
       │
       ├── Exchange
       ├── Instrument
       ├── HTTP
       ├── Retry
       ├── Collector
       └── Validation
```

---

# Immutability

The configuration uses:

```python
@dataclass(frozen=True, slots=True)
```

Therefore, configuration values cannot normally be modified after creation.

This is intentional.

A running collector should not unexpectedly change its:

```text
API endpoint
symbol
timeout
retry policy
```

while it is collecting data.

If a different configuration is required, create a new configuration object.

---

# Exchange Configuration

The configuration contains:

```python
base_url
endpoint
```

These determine where the collector sends requests.

---

# Base URL

Default:

```text
https://eapi.binance.com
```

This represents the exchange API host used by the option-chain collector.

The base URL must:

* Be a string.
* Not be empty.
* Start with `https://` or `http://`.

Example:

```python
OptionChainConfig(
    base_url="https://example.exchange.com"
)
```

---

# Endpoint

Default:

```text
/eapi/v1/exchangeInfo
```

The endpoint must:

* Be a string.
* Not be empty.
* Start with `/`.

This allows the collector to construct the complete request URL from:

```text
base_url + endpoint
```

---

# Why Base URL and Endpoint Are Separate

Keeping them separate makes the collector easier to configure.

```text
base_url
    +
endpoint
    ↓
complete API URL
```

This avoids hard-coding the complete URL throughout the collector.

It also makes testing easier because a mock or test endpoint can be supplied through configuration.

---

# Underlying Symbol

The configuration contains:

```python
underlying_symbol
```

Default:

```text
ETH
```

This represents the underlying asset for the option chain.

The current ETH Bot architecture is focused on ETH derivatives, so ETH is the default.

---

# Symbol Requirements

The underlying symbol must:

* Be a string.
* Not be empty.
* Not contain leading whitespace.
* Not contain trailing whitespace.
* Be uppercase.

Valid:

```text
ETH
```

Invalid:

```text
eth
```

Invalid:

```text
 ETH
```

Invalid:

```text
ETH 
```

Invalid:

```text
""
```

---

# Why Symbol Validation Exists

A configuration error such as:

```text
eth
```

could otherwise silently produce inconsistent requests.

The configuration therefore enforces a normalized representation before the collector starts.

---

# HTTP Configuration

HTTP behavior is controlled by:

```text
timeout
verify_ssl
user_agent
```

---

# Timeout

Default:

```text
10.0 seconds
```

The timeout limits how long an HTTP request can wait.

Example:

```python
OptionChainConfig(
    timeout=15.0
)
```

A timeout must be:

```text
> 0
```

The configuration rejects:

```text
0
```

and:

```text
-5
```

---

# Boolean Protection

The configuration explicitly prevents boolean values from being accepted as numeric settings.

For example:

```python
timeout=True
```

is rejected.

Although Python considers:

```python
True == 1
```

for some numeric operations, treating a boolean as a timeout is a configuration error.

The same protection applies to:

```text
max_retries
retry_delay
backoff_factor
```

---

# SSL Verification

Configuration:

```python
verify_ssl
```

Default:

```text
True
```

This keeps TLS certificate verification enabled.

Normal production configuration should keep:

```text
verify_ssl=True
```

Disabling SSL verification should only be considered in controlled development or testing environments.

---

# User Agent

Configuration:

```python
user_agent
```

Default:

```text
eth-bot-option-chain-collector/1.0
```

The user agent identifies the application making the request.

It must be:

* A string.
* Non-empty.

---

# Retry Configuration

The retry system contains:

```text
max_retries
retry_delay
backoff_factor
retryable_status_codes
```

These settings control how the collector responds to temporary exchange/API failures.

---

# Maximum Retries

Default:

```text
3
```

This represents the maximum number of request attempts used by the collector.

The value must be:

```text
>= 1
```

Invalid:

```python
max_retries=0
```

Invalid:

```python
max_retries=-1
```

---

# Retry Delay

Default:

```text
1.0 second
```

This is the initial delay before a retry.

The value may be zero, meaning retries occur without an intentional delay.

It cannot be negative.

---

# Backoff Factor

Default:

```text
2.0
```

This controls exponential growth of retry delays.

Conceptually:

```text
delay = retry_delay × backoff_factor^(attempt - 1)
```

With the defaults:

```text
1 second
2 seconds
4 seconds
```

---

# Retryable HTTP Status Codes

The default set is:

```text
408
425
429
500
502
503
504
```

These are treated as potentially transient failures.

---

# Meaning of Important Status Codes

### 408

Request timeout.

### 425

Too early / temporary request condition.

### 429

Too many requests / rate limiting.

### 500

Internal server error.

### 502

Bad gateway.

### 503

Service unavailable.

### 504

Gateway timeout.

---

# Why Retryable Status Codes Are Configurable

Different exchanges may expose different transient error behavior.

Keeping the list configurable means the collector does not need to be rewritten when the exchange changes.

Example:

```python
OptionChainConfig(
    retryable_status_codes=frozenset(
        {
            408,
            429,
            500,
            502,
            503,
            504,
        }
    )
)
```

---

# Frozen Set

The configuration uses:

```python
frozenset[int]
```

for retryable status codes.

This is appropriate because the set is configuration rather than runtime state.

It prevents accidental modification.

---

# HTTP Status Validation

Each configured status code must:

* Be an integer.
* Not be a boolean.
* Be between 100 and 599.

Therefore:

```text
200
429
500
```

are valid status codes.

But:

```text
99
```

and:

```text
600
```

are rejected.

---

# Collector Enable Flag

Configuration:

```python
enabled
```

Default:

```text
True
```

This allows the entire option-chain collector to be switched off through configuration.

When:

```text
enabled=False
```

the collector should not make API requests.

---

# Why Enable/Disable Exists

The ETH Bot has multiple market-data collectors.

For example:

```text
OHLCV
Trades
Order Book
Funding Rate
Open Interest
Liquidations
Long/Short Ratio
Option Chain
Greeks
Implied Volatility
Fear & Greed
Whales
On-chain
News
```

Some collectors may be temporarily disabled without deleting their code or changing the pipeline architecture.

---

# Configuration Validation

`OptionChainConfig` validates itself during initialization.

Conceptually:

```text
Create Config
      ↓
Validate Base URL
      ↓
Validate Endpoint
      ↓
Validate Symbol
      ↓
Validate Timeout
      ↓
Validate Retry Count
      ↓
Validate Retry Delay
      ↓
Validate Backoff
      ↓
Validate Status Codes
      ↓
Validate User Agent
      ↓
Validate Boolean Flags
      ↓
Valid Configuration
```

If any rule fails, configuration creation raises an exception.

---

# Configuration Validation Methods

The configuration contains dedicated validation methods:

```text
_validate_base_url()
_validate_endpoint()
_validate_symbol()
_validate_timeout()
_validate_retries()
_validate_retry_delay()
_validate_backoff_factor()
_validate_retryable_status_codes()
_validate_user_agent()
_validate_boolean_options()
```

Keeping these checks separate makes the configuration easier to maintain.

---

# Default Configuration

The module creates:

```python
DEFAULT_OPTION_CHAIN_CONFIG
```

This represents the standard ETH option-chain collector configuration.

Conceptually:

```text
DEFAULT_OPTION_CHAIN_CONFIG
        │
        ├── Binance API
        ├── ETH
        ├── 10-second timeout
        ├── SSL verification
        ├── 3 attempts
        ├── exponential backoff
        └── collector enabled
```

---

# Configuration Factory

The module exposes:

```python
get_option_chain_config()
```

This returns the default configuration.

Example:

```python
config = get_option_chain_config()
```

Then:

```python
collector = OptionChainCollector(
    config=config
)
```

---

# Relationship With Collector

The relationship is:

```text
config.py
    │
    │ configuration
    ▼
collector.py
    │
    │ HTTP request
    ▼
Exchange API
```

The configuration should contain **policy**, while the collector contains **behavior**.

---

# Configuration vs Collector

### Configuration

Defines:

```text
Where?
What?
How long?
How many retries?
Which failures retry?
Enabled?
```

### Collector

Performs:

```text
Build request
Send request
Handle response
Retry
Return result
```

This separation prevents the collector from becoming a large collection of hard-coded constants.

---

# Configuration vs Parser

The configuration does not define parsing rules.

The parser is responsible for converting:

```text
Raw Exchange JSON
```

into:

```text
Normalized Option Chain Records
```

Therefore, parser-specific fields should not be added to this configuration unless they genuinely affect collection behavior.

---

# Configuration vs Validator

The validator handles normalized data-quality rules.

Examples:

```text
valid option type
valid strike
valid expiration
valid bid
valid ask
valid open interest
valid timestamp
```

These belong to:

```text
option_chain/validator.py
```

rather than this collector configuration.

---

# Configuration vs Risk Engine

The configuration does not define trading risk.

It should not contain:

```text
maximum position size
stop loss
take profit
leverage
risk per trade
maximum drawdown
```

Those belong to the trading risk architecture.

---

# Configuration Lifecycle

The intended lifecycle is:

```text
Create Configuration
       ↓
Validate Configuration
       ↓
Create Collector
       ↓
Collect Raw Data
       ↓
Parse
       ↓
Validate Data
       ↓
Store
```

Configuration errors are therefore detected before live data collection starts.

---

# Example Default Configuration

Conceptually:

```python
config = OptionChainConfig()
```

produces:

```text
Base URL:
https://eapi.binance.com

Endpoint:
/eapi/v1/exchangeInfo

Underlying:
ETH

Timeout:
10 seconds

Max retries:
3

Retry delay:
1 second

Backoff:
2x

SSL verification:
enabled

Collector:
enabled
```

---

# Example Custom Configuration

A custom configuration can override selected values:

```python
config = OptionChainConfig(
    timeout=15.0,
    max_retries=5,
    retry_delay=2.0,
    backoff_factor=2.0,
)
```

All unspecified values retain their defaults.

---

# Testing Configuration

Recommended test location:

```text
D:\Sachin Chakrawarti\eth_bot\
tests\
└── collectors\
    └── option_chain\
        └── test_config.py
```

Recommended tests include:

```text
default configuration
custom configuration
empty base URL
invalid base URL
invalid endpoint
empty endpoint
lowercase symbol
empty symbol
symbol whitespace
zero timeout
negative timeout
boolean timeout
zero retries
negative retries
boolean retries
negative retry delay
negative backoff factor
invalid HTTP status code
boolean HTTP status code
empty user agent
invalid verify_ssl
invalid enabled flag
```

---

# Configuration Design Principle

The configuration should remain focused on **collection behavior**.

A useful boundary is:

```text
config.py
    ↓
Operational configuration

collector.py
    ↓
Data acquisition

parser.py
    ↓
Data normalization

validator.py
    ↓
Data quality

analytics
    ↓
Derived information

strategy
    ↓
Trading decisions

risk engine
    ↓
Trade authorization
```

---

# Final Responsibility

`option_chain/config.py` has one core responsibility:

> **Define and validate the operational configuration required by the ETH option-chain collector, including exchange endpoint, underlying symbol, HTTP behavior, retry policy, and collector state, while keeping collection behavior separate from parsing, validation, analytics, and trading logic.**
