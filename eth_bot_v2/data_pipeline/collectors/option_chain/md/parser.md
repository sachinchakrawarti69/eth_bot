# Option Chain Parser

## Overview

`option_chain/parser.py` converts raw exchange option-chain responses into normalized internal records.

Its responsibility is **data normalization**, not data collection, validation, analytics, or trading.

```text
Exchange API
     ↓
collector.py
     ↓
Raw API Response
     ↓
parser.py
     ↓
OptionChainRecord
     ↓
validator.py
     ↓
Validated Option Data
```

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

The parser is responsible for:

* Extracting option records from API responses.
* Supporting common response container structures.
* Normalizing field names.
* Normalizing option types.
* Converting numeric values to `float`.
* Converting timestamps to Unix milliseconds.
* Normalizing symbols.
* Preserving the original raw record.
* Creating `OptionChainRecord` objects.

---

# Non-Responsibilities

The parser does **not**:

* Make API requests.
* Retry HTTP requests.
* Perform API authentication.
* Validate business rules.
* Calculate Greeks.
* Calculate implied volatility.
* Calculate technical indicators.
* Generate ML features.
* Generate trading signals.
* Approve or reject trades.
* Execute orders.

The architecture remains:

```text
Collector
    ↓
Parser
    ↓
Validator
    ↓
Analytics
    ↓
Dataset Generator
    ↓
Models
    ↓
Strategy
    ↓
Risk Engine
    ↓
Execution
```

---

# Main Class

The main parser class is:

```python
OptionChainParser
```

It provides methods for parsing:

* Complete API responses.
* Individual option records.
* Multiple option records.
* Expiration timestamps.
* General timestamps.

---

# Normalized Record

The parser produces:

```python
OptionChainRecord
```

This is the normalized internal representation of one option contract.

The record contains:

```text
symbol
option_type
strike_price
expiry_timestamp
bid_price
ask_price
mark_price
bid_quantity
ask_quantity
volume
open_interest
last_price
underlying_price
contract_id
timestamp
raw
```

---

# Required Fields

The parser requires these fields:

```text
symbol
option_type
strike_price
expiry_timestamp
```

If any required field is missing, parsing fails for that record.

These fields identify the basic structure of an option contract.

---

# Optional Fields

The following fields are optional:

```text
bid_price
ask_price
mark_price
bid_quantity
ask_quantity
volume
open_interest
last_price
underlying_price
contract_id
timestamp
```

Missing optional values become:

```python
None
```

---

# Symbol

The parser normalizes the option symbol.

For example:

```text
eth-240101-3000-c
```

becomes:

```text
ETH-240101-3000-C
```

The parser:

1. Confirms the value is a string.
2. Removes surrounding whitespace.
3. Converts it to uppercase.
4. Rejects an empty result.

---

# Option Type

The parser normalizes option types to:

```text
CALL
PUT
```

Supported representations include:

```text
C
CALL
P
PUT
```

Examples:

```text
C     → CALL
CALL  → CALL
P     → PUT
PUT   → PUT
```

Unknown option types raise:

```python
OptionChainParseError
```

---

# Strike Price

The strike price is converted to:

```python
float
```

For example:

```text
"3500"
```

becomes:

```text
3500.0
```

The parser only performs type conversion.

It does not determine whether the strike is economically valid.

That belongs to the validator.

---

# Expiration Timestamp

The expiration timestamp is required.

The parser converts it to:

```text
Unix milliseconds
```

The parser supports:

* Numeric seconds.
* Numeric milliseconds.
* Numeric strings.
* ISO-8601 timestamps.
* Python `datetime` objects.

---

# Timestamp Normalization

For example:

```text
1700000000
```

is interpreted as seconds and converted to:

```text
1700000000000
```

A value already expressed in milliseconds remains in millisecond precision.

---

# ISO-8601 Support

The parser also supports values such as:

```text
2026-08-05T12:00:00Z
```

and converts them to Unix milliseconds.

A timezone-naive `datetime` is interpreted as UTC.

---

# Optional Timestamp

The normal market-data timestamp is optional.

If it is missing:

```python
timestamp = None
```

If it is present, it is normalized to Unix milliseconds.

---

# Numeric Fields

The parser converts numeric market fields to `float`.

Examples:

```text
"12.50"
```

becomes:

```text
12.5
```

This applies to fields such as:

```text
bid_price
ask_price
mark_price
bid_quantity
ask_quantity
volume
open_interest
last_price
underlying_price
```

---

# Numeric Validation Boundary

The parser only asks:

> Can this value be represented as a numeric value?

It does not ask:

> Is this numeric value valid for the market?

For example, a negative price may still be parsed as a number.

Whether that value should be accepted belongs to:

```text
option_chain/validator.py
```

This separation is important.

---

# Raw Record Preservation

Each normalized record contains:

```python
raw
```

which stores the original raw record.

Conceptually:

```text
Raw API Record
      │
      ├───────────────┐
      ↓               ↓
Normalized fields     raw
```

This is useful for:

* Debugging.
* Reprocessing.
* Auditing.
* Investigating exchange-format changes.
* Reconstructing normalization problems.

---

# Field Aliases

Different APIs may use different field names.

The parser therefore defines:

```python
FIELD_ALIASES
```

Examples:

```text
strikePrice
strike_price
strike
```

can all map to:

```text
strike_price
```

Similarly:

```text
bidPrice
bid_price
bid
```

map to:

```text
bid_price
```

---

# Supported Field Mapping

The parser maps common aliases for:

```text
symbol
option_type
strike_price
expiry_timestamp
bid_price
ask_price
mark_price
bid_quantity
ask_quantity
volume
open_interest
last_price
underlying_price
contract_id
timestamp
```

---

# Why Field Aliases Matter

The rest of the ETH Bot should not depend on exchange-specific naming.

For example, downstream code should use:

```python
record.strike_price
```

rather than knowing whether the exchange returned:

```text
strikePrice
```

or:

```text
strike_price
```

This creates a stable internal schema.

---

# Response Extraction

The parser can handle several common response structures.

For example:

```json
{
    "optionSymbols": [...]
}
```

or:

```json
{
    "data": [...]
}
```

or:

```json
{
    "options": [...]
}
```

or a direct list:

```json
[
    {...},
    {...}
]
```

The parser extracts the actual option records before normalization.

---

# Candidate Response Containers

The parser looks for common containers such as:

```text
optionSymbols
option_symbols
options
data
result
contracts
```

This is intended to make the parser tolerant of different API response wrappers.

---

# Direct Single Record

If the response itself looks like a single option record, the parser can treat it as a one-record response.

For example:

```text
{
    symbol: ...,
    strikePrice: ...,
    expiryDate: ...
}
```

becomes:

```text
[
    OptionChainRecord(...)
]
```

---

# Record Extraction Flow

```text
Raw Response
     ↓
Is it a list?
     │
     ├── Yes → records
     │
     └── No
          ↓
       Is it a mapping?
          │
          ├── No → Error
          │
          └── Yes
               ↓
        Search known containers
               ↓
        Extract option records
               ↓
        Normalize each record
```

---

# `parse()`

The primary method is:

```python
parse(response)
```

It:

1. Extracts records.
2. Iterates through each record.
3. Parses each record.
4. Returns a list of `OptionChainRecord`.

Example:

```python
parser = OptionChainParser()

records = parser.parse(raw_response)
```

The result is:

```text
list[OptionChainRecord]
```

---

# `parse_record()`

The method:

```python
parse_record(raw_record)
```

normalizes one option record.

Its basic flow is:

```text
Raw Record
    ↓
Extract symbol
    ↓
Normalize option type
    ↓
Convert strike
    ↓
Convert expiry
    ↓
Convert optional fields
    ↓
Preserve raw record
    ↓
OptionChainRecord
```

---

# `parse_many()`

The method:

```python
parse_many(records)
```

parses an iterable containing individual records.

This is useful when the caller already extracted the option records from the API response.

---

# `parse_expiry()`

The method:

```python
parse_expiry(value)
```

normalizes an expiration value to Unix milliseconds.

This exposes timestamp conversion separately for callers that need it.

---

# `parse_timestamp()`

The method:

```python
parse_timestamp(value)
```

normalizes a general timestamp to Unix milliseconds.

---

# Parsing Errors

The parser defines:

```python
OptionChainParseError
```

which extends:

```python
ValueError
```

This gives callers a specific exception type for normalization failures.

---

# Missing Required Field

For example, if `strike_price` is missing:

```text
Raw Record
    ↓
strike_price missing
    ↓
OptionChainParseError
```

The error includes the record index when parsing a complete response.

---

# Invalid Option Type

For example:

```text
option_type = "X"
```

results in:

```text
OptionChainParseError
```

because only:

```text
CALL
PUT
```

are supported after normalization.

---

# Invalid Numeric Value

For example:

```text
strike_price = "invalid"
```

cannot be converted to `float`.

The parser raises:

```text
OptionChainParseError
```

---

# Invalid Timestamp

An invalid timestamp such as:

```text
"not-a-date"
```

results in a parsing error.

The parser does not silently create a fake timestamp.

---

# Boolean Protection

Boolean values are explicitly rejected for numeric fields.

For example:

```python
strike_price=True
```

does not become:

```text
1.0
```

This prevents subtle schema corruption.

---

# Optional Empty Values

For optional numeric strings:

```text
""
```

is treated as missing:

```python
None
```

This allows incomplete optional market fields to be represented without confusing an empty string with a numeric value.

---

# Parser and Validator Boundary

The distinction is:

### Parser

```text
"3500"
    ↓
3500.0
```

### Validator

```text
3500.0
    ↓
Is this an acceptable strike?
```

Similarly:

### Parser

```text
"C"
    ↓
CALL
```

### Validator

```text
CALL
    ↓
Is CALL valid for this record?
```

---

# Why This Separation Matters

If parsing and validation are mixed together, the parser becomes tightly coupled to trading-domain rules.

The current architecture instead keeps:

```text
Syntax normalization
```

separate from:

```text
Data-quality validation
```

This makes the system easier to test and maintain.

---

# Parser and Greeks

The parser does not calculate:

```text
Delta
Gamma
Theta
Vega
Rho
```

The parser only prepares the normalized market data required by downstream calculations.

The flow is:

```text
Option Chain
     ↓
Parser
     ↓
Normalized Option Data
     ↓
Greeks Engine
```

---

# Parser and Implied Volatility

The parser also does not calculate implied volatility.

The expected architecture is:

```text
Raw Option Data
       ↓
Parser
       ↓
Validated Option Data
       ↓
Market Price
       ↓
Implied Volatility Engine
       ↓
IV
```

---

# Parser and ML Features

The parser does not create model features such as:

```text
IV rank
IV percentile
put/call ratio
skew
term structure
volatility spread
order-flow features
momentum
trend
```

Those belong to downstream analytics and dataset-generation layers.

---

# Parser and Trading Decisions

The parser must never produce:

```text
BUY
SELL
LONG
SHORT
HOLD
REJECT
```

It produces data only.

---

# Convenience Function

The module provides:

```python
parse_option_chain(response)
```

This creates a parser internally and parses the response.

Conceptually:

```python
records = parse_option_chain(
    raw_response
)
```

---

# Single Record Convenience Function

The module also provides:

```python
parse_option_chain_record(record)
```

which parses one raw record.

---

# Multiple Records Convenience Function

The module provides:

```python
parse_option_chain_records(records)
```

which parses multiple records.

---

# Data Flow Through the ETH Bot

The option-chain parser sits here:

```text
                     Exchange
                        │
                        ▼
              ┌─────────────────┐
              │    Collector    │
              └────────┬────────┘
                       │
                  Raw JSON
                       │
                       ▼
              ┌─────────────────┐
              │     Parser      │
              └────────┬────────┘
                       │
              OptionChainRecord
                       │
                       ▼
              ┌─────────────────┐
              │    Validator    │
              └────────┬────────┘
                       │
                Validated Data
                       │
                       ▼
              ┌─────────────────┐
              │    Analytics    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Dataset Builder │
              └────────┬────────┘
                       │
                       ▼
                  ML / DL Models
```

---

# Testing

Recommended test location:

```text
D:\Sachin Chakrawarti\eth_bot\
tests\
└── collectors\
    └── option_chain\
        └── test_parser.py
```

Recommended tests include:

```text
parse direct list
parse optionSymbols response
parse data response
parse options response
parse single record
parse multiple records
symbol normalization
option type C
option type CALL
option type P
option type PUT
invalid option type
strike conversion
optional numeric conversion
missing optional values
expiry in seconds
expiry in milliseconds
expiry ISO-8601
datetime expiry
invalid timestamp
missing required field
invalid numeric value
boolean numeric value
raw record preservation
```

---

# Example Normalization

Conceptually, an exchange record like:

```json
{
    "symbol": "ETH-26AUG-3500-C",
    "optionType": "C",
    "strikePrice": "3500",
    "expiryDate": 1787740800000,
    "bidPrice": "120.5",
    "askPrice": "125.0",
    "volume": "42",
    "openInterest": "1000"
}
```

is normalized into a structure conceptually equivalent to:

```text
symbol:
ETH-26AUG-3500-C

option_type:
CALL

strike_price:
3500.0

expiry_timestamp:
1787740800000

bid_price:
120.5

ask_price:
125.0

volume:
42.0

open_interest:
1000.0
```

The original exchange record remains available through:

```python
record.raw
```

---

# Important Design Principle

The parser follows:

> **Normalize structure without making trading decisions.**

It converts inconsistent external representations into a stable internal representation while avoiding domain-level decisions.

---

# Final Responsibility

`option_chain/parser.py` has one core responsibility:

> **Convert raw exchange option-chain responses into consistent `OptionChainRecord` objects by extracting records, normalizing field names and option types, converting numeric values and timestamps, and preserving the original raw data, while leaving data-quality validation, analytics, modeling, risk management, and execution to downstream components.**
