# Long/Short Ratio Parser

## Overview

`parser.py` is responsible for converting raw exchange **ETH futures long/short ratio** responses into the normalized internal data structure used by the data pipeline.

The parser sits between the collector and validator:

```text
Exchange API
     ↓
collector.py
     ↓
Raw Response
     ↓
parser.py
     ↓
Normalized Records
     ↓
validator.py
     ↓
Validated Data
```

The parser performs **normalization**, not business validation or trading analysis.

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

# Primary Responsibility

The parser is responsible for:

* Extracting records from raw API responses.
* Handling common response wrappers.
* Mapping exchange field names to internal names.
* Converting numeric values to `float`.
* Normalizing symbols.
* Normalizing periods.
* Normalizing timestamps.
* Preserving optional source metadata.
* Parsing individual records.
* Parsing multiple records.
* Parsing paginated responses.

---

# Non-Responsibilities

The parser does **not**:

* Make API requests.
* Handle authentication.
* Implement API retry logic.
* Decide whether data is valid for trading.
* Calculate indicators.
* Generate features.
* Predict price direction.
* Predict volatility.
* Generate trading signals.
* Approve trades.
* Reject trades.
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

Analytics
    ↓
Calculate

Dataset Generator
    ↓
Prepare ML Data

Models
    ↓
Predict
```

---

# Main Class

The primary parser class is:

```python
LongShortRatioParser
```

It provides methods for parsing:

* Individual records.
* Complete API responses.
* Multiple records.
* Multiple pages.

---

# Normalized Record

The parser produces:

```python
LongShortRatioRecord
```

The normalized record contains:

```text
symbol
period
timestamp
long_account
short_account
long_short_ratio
source
event_time
```

---

# Record Fields

| Field              | Type          | Description                    |
| ------------------ | ------------- | ------------------------------ |
| `symbol`           | `str`         | Futures symbol                 |
| `period`           | `str`         | Aggregation period             |
| `timestamp`        | `int`         | Unix timestamp in milliseconds |
| `long_account`     | `float`       | Long-account value             |
| `short_account`    | `float`       | Short-account value            |
| `long_short_ratio` | `float`       | Long/short ratio               |
| `source`           | `str \| None` | Optional source identifier     |
| `event_time`       | `int \| None` | Optional event timestamp       |

---

# Why Use a Normalized Record?

Exchange APIs can represent the same concept using different field names.

For example:

```text
longAccount
```

or:

```text
long_account
```

The internal pipeline should not need to understand every exchange-specific naming convention.

Therefore:

```text
Exchange Format
      ↓
Parser
      ↓
Internal Format
```

The rest of the system works with the internal format.

---

# Field Aliases

The parser defines aliases for common fields.

## Symbol

Supported aliases include:

```text
symbol
s
```

Both map to:

```text
symbol
```

---

## Period

Supported aliases:

```text
period
interval
i
```

They map to:

```text
period
```

---

## Timestamp

Supported aliases:

```text
timestamp
time
T
updateTime
update_time
```

They map to:

```text
timestamp
```

---

## Long Account

Supported aliases:

```text
longAccount
long_account
long
longRatio
```

They map to:

```text
long_account
```

---

## Short Account

Supported aliases:

```text
shortAccount
short_account
short
shortRatio
```

They map to:

```text
short_account
```

---

## Long/Short Ratio

Supported aliases:

```text
longShortRatio
long_short_ratio
ratio
```

They map to:

```text
long_short_ratio
```

---

## Event Time

Supported aliases:

```text
eventTime
event_time
E
```

They map to:

```text
event_time
```

---

# Response Wrappers

The parser supports common API response structures.

For example:

```json
{
  "data": [...]
}
```

or:

```json
{
  "result": [...]
}
```

or:

```json
{
  "rows": [...]
}
```

or:

```json
{
  "records": [...]
}
```

The parser extracts the underlying list before parsing records.

---

# Direct List Response

The parser also accepts:

```python
[
    {...},
    {...},
    {...}
]
```

directly.

---

# Single Record Response

If the API returns a single record instead of a list, the parser can recognize it as a record when known fields are present.

Conceptually:

```text
Raw Mapping
     ↓
Looks like record?
     ↓
Yes
     ↓
[record]
```

---

# `parse()`

The main method for a single record is:

```python
parse(raw_record)
```

Example:

```python
record = parser.parse(raw_record)
```

The method:

1. Reads exchange fields.
2. Resolves aliases.
3. Applies defaults where appropriate.
4. Normalizes values.
5. Creates `LongShortRatioRecord`.

---

# `parse_response()`

Used for complete API responses:

```python
parse_response(response)
```

Flow:

```text
Raw API Response
       ↓
Extract Records
       ↓
parse_many()
       ↓
Normalized Records
```

---

# `parse_many()`

Used for multiple records:

```python
parse_many(records)
```

It iterates through each raw record and calls:

```python
parse(record)
```

The result is:

```python
list[LongShortRatioRecord]
```

---

# Strict Mode

The parser supports:

```python
strict=True
```

In strict mode, a malformed record raises the parsing exception immediately.

This is useful during:

* Development.
* Testing.
* Debugging.
* Schema changes.

---

# Non-Strict Mode

With:

```python
strict=False
```

malformed records can be skipped when parsing multiple records.

This is useful when processing large historical datasets where one malformed exchange record should not necessarily stop the entire ingestion batch.

---

# `parse_pages()`

Historical collection may return multiple API pages.

The parser supports:

```python
parse_pages(pages)
```

Conceptually:

```text
Page 1
 ↓
Parse

Page 2
 ↓
Parse

Page 3
 ↓
Parse

      ↓

Combined Records
```

---

# Symbol Normalization

Symbols are normalized using:

```text
strip()
+
upper()
```

For example:

```text
" ethusdt "
```

becomes:

```text
ETHUSDT
```

An empty symbol is rejected.

---

# Default Symbol

The parser defaults to:

```text
ETHUSDT
```

If the exchange response does not contain a symbol, the parser can use the configured default symbol.

This supports APIs that identify the instrument through request parameters rather than repeating it in every returned record.

---

# Period Normalization

Periods are normalized to lowercase.

For example:

```text
5M
```

becomes:

```text
5m
```

Similarly:

```text
1H
```

becomes:

```text
1h
```

The parser normalizes the representation but does not perform the full business validation of supported intervals.

That responsibility belongs to the configuration/validator layer.

---

# Numeric Conversion

Exchange APIs frequently return numeric values as strings.

For example:

```json
{
  "longAccount": "0.6215"
}
```

The parser converts:

```text
"0.6215"
```

to:

```python
0.6215
```

The normalized fields are stored as `float`.

---

# Numeric Fields

The parser converts:

```text
long_account
short_account
long_short_ratio
```

to floating-point values.

---

# Numeric String Support

Both are accepted:

```text
"0.6215"
```

and:

```text
0.6215
```

The resulting internal representation is:

```python
0.6215
```

---

# Finite Number Handling

The parser rejects non-finite values such as:

```text
NaN
Infinity
-Infinity
```

This protects the normalized dataset from immediately introducing invalid numeric values.

Additional domain validation remains the responsibility of `validator.py`.

---

# Boolean Protection

Python considers:

```python
True
```

to be an integer.

The parser explicitly prevents boolean values from being interpreted as numeric market data.

For example:

```text
True
```

must not become:

```text
1.0
```

---

# Timestamp Normalization

The parser converts timestamps into:

```text
Unix milliseconds
```

This gives the entire pipeline a consistent timestamp representation.

---

# Supported Timestamp Types

The parser supports:

```text
Unix seconds
Unix milliseconds
datetime
ISO-8601 string
numeric timestamp strings
```

---

# Unix Seconds

Example:

```text
1754006400
```

is interpreted as seconds and converted to:

```text
1754006400000
```

---

# Unix Milliseconds

Example:

```text
1754006400000
```

is preserved as milliseconds.

---

# Datetime

A Python `datetime` can be converted into the normalized Unix-millisecond representation.

Timezone-aware datetimes are handled directly.

Naive datetimes are interpreted as UTC.

---

# ISO-8601

The parser supports strings such as:

```text
2026-08-05T10:30:00Z
```

and timezone-aware ISO timestamps.

The resulting value is converted into Unix milliseconds.

---

# Timestamp Validation

The parser rejects:

```text
negative timestamps
empty timestamp strings
invalid ISO timestamps
non-finite numeric timestamps
unsupported timestamp types
```

---

# Event Time

Some exchange responses provide an additional event timestamp.

The parser maps:

```text
eventTime
event_time
E
```

to:

```text
event_time
```

This field is optional.

If it is absent:

```text
event_time = None
```

---

# Source Metadata

The parser optionally supports:

```text
source
```

Source metadata can identify where the data originated.

For example:

```text
binance
```

The parser can receive a default source during initialization.

---

# Source Normalization

Source values are:

```text
strip()
```

and preserved as strings.

Empty source values are rejected when explicitly provided.

---

# Error Handling

The parser distinguishes malformed input from valid normalized data.

Typical errors include:

```text
TypeError
ValueError
KeyError
```

Examples:

```text
invalid response type
invalid symbol
invalid period
missing timestamp
invalid numeric field
invalid timestamp
```

---

# Parser vs Validator

It is important not to duplicate responsibilities.

### Parser

```text
"0.6215"
    ↓
0.6215
```

### Validator

```text
0.6215
    ↓
Is this value acceptable?
```

The parser answers:

> "How do I represent this exchange value internally?"

The validator answers:

> "Is this normalized record acceptable?"

---

# Parser vs Analytics

The parser must not calculate analytics such as:

```text
long percentage
short percentage
ratio change
ratio moving average
positioning momentum
positioning divergence
extreme positioning
```

Those belong downstream.

---

# Parser vs ML

The parser must not produce model predictions.

It only creates normalized market-data records.

The flow is:

```text
Raw Data
   ↓
Parser
   ↓
Normalized Data
   ↓
Validator
   ↓
Analytics
   ↓
Dataset Generator
   ↓
ML Model
```

---

# Parser vs Risk Engine

The parser has no relationship with trade approval.

It must never perform:

```text
BUY
SELL
HOLD
REJECT
POSITION SIZE
STOP LOSS
TAKE PROFIT
```

Those belong to downstream trading components.

---

# Example Raw Record

An exchange response may resemble:

```json
{
  "symbol": "ETHUSDT",
  "longShortRatio": "1.52",
  "longAccount": "0.603",
  "shortAccount": "0.397",
  "timestamp": 1754397000000
}
```

The parser converts this into an internal record equivalent to:

```text
symbol            → ETHUSDT
period            → 5m
timestamp         → 1754397000000
long_account      → 0.603
short_account     → 0.397
long_short_ratio  → 1.52
```

---

# Example Pipeline

```text
Exchange Response
       ↓
{
  "longAccount": "0.603",
  "shortAccount": "0.397",
  "longShortRatio": "1.52"
}
       ↓
LongShortRatioParser
       ↓
LongShortRatioRecord
       ↓
LongShortRatioValidator
```

---

# Parser Initialization

The parser can be initialized with:

```text
default_symbol
default_period
source
strict
```

For example:

```python
parser = LongShortRatioParser(
    default_symbol="ETHUSDT",
    default_period="5m",
    source="binance",
    strict=True,
)
```

---

# Historical Data

The parser is designed to work with historical data.

The collector can return:

```text
Page 1
Page 2
Page 3
...
```

The parser converts these pages into one normalized collection.

This makes it suitable for the project's historical model-training pipeline.

---

# Duplicate Handling

The parser does not perform deduplication.

If two records have the same timestamp:

```text
t1
t1
```

they remain separate records.

Duplicate detection and data-quality decisions belong to `validator.py` or the downstream data-quality layer.

---

# Sorting

The parser does not sort records.

The collector may return records in exchange-defined order.

If ordering is required, it should be handled by the appropriate downstream validation or processing layer.

This keeps the parser focused on normalization.

---

# Parser Output

The output type is:

```python
list[LongShortRatioRecord]
```

for multiple records.

A single record produces:

```python
LongShortRatioRecord
```

---

# Relationship With Dataset Generator

The parser output eventually feeds:

```text
Dataset Generator
```

The pipeline becomes:

```text
Exchange
   ↓
Collector
   ↓
Parser
   ↓
Validator
   ↓
Processed Storage
   ↓
Indicators Analytics
   ↓
Dataset Generator
   ↓
Tabular / Sequence / Attention Dataset
```

---

# Relationship With ML Datasets

Long/short ratio can become one of many model inputs.

For example:

```text
OHLCV
Open Interest
Funding Rate
Long/Short Ratio
Liquidations
Order Book
Trades
Options Data
       ↓
Indicators Analytics
       ↓
Feature Dataset
       ↓
Model Dataset
```

The parser itself should remain unaware of how these features are eventually consumed.

---

# Testing

Recommended test location:

```text
D:\Sachin Chakrawarti\eth_bot\
tests\
└── collectors\
    └── long_short_ratio\
        └── test_parser.py
```

---

# Recommended Tests

Tests should cover:

```text
single record parsing
multiple record parsing
wrapped response parsing
list response parsing
single-record response parsing
symbol normalization
period normalization
numeric string conversion
numeric conversion
boolean rejection
NaN rejection
Infinity rejection
Unix-second timestamps
Unix-millisecond timestamps
datetime timestamps
ISO timestamps
invalid timestamps
event time parsing
source parsing
strict mode
non-strict mode
empty response
multiple pages
malformed records
```

---

# Parser Design

The parser follows:

```text
Raw Exchange Schema
        ↓
Field Alias Resolution
        ↓
Type Conversion
        ↓
Normalization
        ↓
LongShortRatioRecord
        ↓
Validator
```

---

# Data Pipeline Position

```mermaid id="4xoc0w"
flowchart LR

Exchange["Exchange API"]

Collector["collector.py"]

Parser["parser.py"]

Validator["validator.py"]

Storage["Processed Storage"]

Analytics["Indicators Analytics"]

Dataset["Dataset Generator"]

Models["ML / DL Models"]

Exchange
    -->
Collector
    -->
Parser
    -->
Validator
    -->
Storage
    -->
Analytics
    -->
Dataset
    -->
Models
```

---

# Design Principle

The central principle of `parser.py` is:

> **Normalize exchange data without interpreting it.**

The parser creates a stable internal representation so that the rest of the ETH futures data pipeline does not depend directly on exchange-specific response formats.

---

# Final Responsibility

`long_short_ratio/parser.py` has one primary responsibility:

> **Convert raw ETH futures long/short ratio API responses into consistent internal `LongShortRatioRecord` objects by extracting fields, resolving exchange-specific aliases, converting numeric values, and normalizing timestamps, symbols, and periods, while leaving data-quality validation, analytics, strategy, risk management, and execution to downstream components.**
