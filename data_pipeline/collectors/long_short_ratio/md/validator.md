# Long/Short Ratio Validator

## Overview

`validator.py` validates normalized ETH futures long/short ratio records before they enter processed storage or downstream analytics.

The validator operates **after `parser.py`**.

```text
Exchange API
    ↓
collector.py
    ↓
parser.py
    ↓
validator.py
    ↓
processed storage
    ↓
Indicators Analytics
    ↓
Dataset Generator
    ↓
ML / DL Models
```

Its purpose is to answer:

> **Is this normalized long/short ratio record structurally and numerically acceptable for the next stage of the data pipeline?**

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

# Primary Responsibilities

The validator checks:

* Record type.
* Symbol.
* Period.
* Timestamp.
* Long-account value.
* Short-account value.
* Long/short ratio.
* Numeric finiteness.
* Negative values.
* Ratio consistency.
* Duplicate timestamps.
* Timestamp ordering.
* Batch-level structural integrity.

---

# Non-Responsibilities

The validator does **not**:

* Call exchange APIs.
* Parse raw API JSON.
* Normalize exchange-specific field names.
* Calculate indicators.
* Generate ML features.
* Predict market direction.
* Predict volatility.
* Generate trading signals.
* Decide whether to enter a position.
* Size positions.
* Reject trades.
* Execute orders.

The important separation is:

```text
Parser
    ↓
"What does this raw exchange value mean internally?"

Validator
    ↓
"Is this normalized data acceptable?"

Analytics
    ↓
"What information can we calculate from it?"

Strategy
    ↓
"Is there a trading opportunity?"

Risk Engine
    ↓
"Can this trade be allowed?"
```

---

# Main Class

The primary validator class is:

```python
LongShortRatioValidator
```

It validates instances of:

```python
LongShortRatioRecord
```

from:

```text
parser.py
```

---

# Validation Configuration

Validation rules are controlled by:

```python
LongShortRatioValidationConfig
```

This separates validation policy from validation logic.

The configuration contains rules such as:

```text
expected symbol
supported periods
required fields
negative-value rules
zero-value rules
ratio consistency
timestamp rules
duplicate timestamp policy
timestamp ordering
numeric tolerance
```

---

# Default Symbol

The default expected symbol is:

```text
ETHUSDT
```

This is intentional because the current data pipeline is designed around ETH futures.

A record for another instrument, such as:

```text
BTCUSDT
```

will fail the default symbol validation.

---

# Supported Periods

The default configuration supports:

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

The validator checks whether the normalized period belongs to the configured set.

---

# Required Fields

The configuration allows required-field policies for:

```text
symbol
period
timestamp
long_account
short_account
long_short_ratio
```

By default, these fields are required.

---

# Validation Result

The validator returns:

```python
ValidationResult
```

for a single record.

It contains:

```text
valid
errors
```

For example:

```text
valid = True
errors = ()
```

or:

```text
valid = False
errors = (...)
```

---

# Validation Error

Individual failures are represented by:

```python
ValidationError
```

Each error contains:

```text
field
message
index
```

`index` is used when the error belongs to a particular record in a batch.

---

# Batch Validation Result

Multiple records return:

```python
BatchValidationResult
```

It provides:

```text
valid
total_records
valid_records
invalid_records
errors
```

It also exposes:

```text
error_count
validation_rate
```

---

# Single Record Validation

The main method is:

```python
validate(record)
```

Conceptually:

```text
LongShortRatioRecord
        ↓
Symbol
        ↓
Period
        ↓
Timestamp
        ↓
Long Account
        ↓
Short Account
        ↓
Ratio
        ↓
Consistency
        ↓
ValidationResult
```

---

# Symbol Validation

The validator checks that the symbol:

1. Is a string.
2. Is not empty.
3. Is normalized.
4. Matches the expected ETH futures symbol.

Example of valid:

```text
ETHUSDT
```

Example of invalid:

```text
ethusdt
```

because the parser's normalized output is expected to use uppercase.

Another invalid example:

```text
BTCUSDT
```

when the expected symbol is `ETHUSDT`.

---

# Period Validation

The validator checks:

* Type.
* Empty values.
* Normalization.
* Supported interval.

For example:

```text
5m
```

is valid.

But:

```text
5M
```

is rejected if it reaches the validator without parser normalization.

Likewise:

```text
unknown
```

is rejected because it is not a supported period.

---

# Timestamp Validation

The validator expects:

```text
integer Unix timestamp in milliseconds
```

For example:

```text
1754397000000
```

is structurally valid.

The validator rejects:

```text
None
```

```text
"1754397000000"
```

```text
1754397000.5
```

when the normalized record is expected to contain an integer.

---

# Positive Timestamp

The default configuration requires timestamps greater than zero.

Therefore:

```text
0
```

and:

```text
-1
```

are invalid.

---

# Long Account Validation

`long_account` must:

* Be numeric.
* Not be boolean.
* Be finite.
* Not be negative by default.
* Respect the configured zero-value policy.

Example:

```text
0.603
```

is valid.

Example:

```text
-0.20
```

is invalid by default.

---

# Short Account Validation

`short_account` follows the same validation policy.

Example:

```text
0.397
```

is valid.

Negative values are rejected by default.

---

# Long/Short Ratio Validation

`long_short_ratio` must:

* Be numeric.
* Not be boolean.
* Be finite.
* Not be negative by default.

Example:

```text
1.52
```

is valid.

Example:

```text
-1.52
```

is invalid by default.

---

# Finite Number Validation

The validator rejects:

```text
NaN
Infinity
-Infinity
```

This prevents invalid numerical values from entering downstream datasets.

---

# Boolean Protection

Boolean values are explicitly rejected as numeric values.

For example:

```python
True
```

must not be interpreted as:

```text
1
```

and:

```python
False
```

must not be interpreted as:

```text
0
```

This is especially important because Python treats `bool` as a subclass of `int`.

---

# Ratio Consistency

The validator can optionally check whether:

```text
long_short_ratio
```

is mathematically consistent with:

```text
long_account / short_account
```

The default configuration enables this check.

Conceptually:

```text
long_account
      ÷
short_account
      ↓
expected ratio
      ↓
compare with supplied ratio
```

---

# Ratio Tolerance

Exchange APIs may round values.

Therefore, exact equality is not always required.

The configuration provides:

```text
ratio_tolerance
```

with a default value of:

```text
1e-9
```

This prevents tiny floating-point differences from incorrectly failing validation.

---

# Zero Short Account

If:

```text
short_account = 0
```

the validator does not attempt:

```text
long_account / 0
```

during ratio-consistency validation.

This avoids division-by-zero errors.

Whether zero itself is acceptable is controlled separately by:

```text
allow_zero_short_account
```

---

# Zero Long Account

Whether:

```text
long_account = 0
```

is acceptable is controlled by:

```text
allow_zero_long_account
```

The default configuration allows zero.

---

# Negative Values

The default policy rejects negative:

```text
long_account
short_account
long_short_ratio
```

This represents a basic domain sanity check.

---

# Batch Validation

The method:

```python
validate_many(records)
```

validates an entire collection.

For example:

```text
Record 1 → valid
Record 2 → valid
Record 3 → invalid
Record 4 → valid
```

The result reports:

```text
total_records = 4
valid_records = 3
invalid_records = 1
```

---

# Duplicate Timestamp Detection

The validator can detect duplicate timestamps.

Example:

```text
10:00 → record A
10:00 → record B
```

If duplicate timestamps are not allowed, the second occurrence generates a validation error.

This is important for time-series data because duplicate observations can distort:

* Rolling indicators.
* Training windows.
* Sequence construction.
* Aggregations.
* Backtests.

---

# Timestamp Ordering

The default configuration requires timestamps to be monotonically increasing.

Valid:

```text
10:00
10:05
10:10
10:15
```

Invalid:

```text
10:00
10:10
10:05
10:15
```

The second sequence contains a backward timestamp transition.

---

# Why Timestamp Ordering Matters

The long/short ratio is time-series data.

Incorrect ordering can cause downstream calculations to use future observations before earlier observations.

This can contaminate:

* Feature engineering.
* Sequence datasets.
* Backtesting.
* Model training.
* Signal evaluation.

Therefore, ordering is an important data-quality check.

---

# Duplicate vs Ordering

These are separate checks.

### Duplicate

```text
10:00
10:00
```

Two records share the same timestamp.

### Non-Monotonic

```text
10:00
10:10
10:05
```

The timestamp moves backward.

A dataset can pass one check and fail the other.

---

# `is_valid()`

For simple boolean validation:

```python
is_valid(record)
```

returns:

```text
True
```

or:

```text
False
```

This is useful when the caller does not need detailed error information.

---

# `is_batch_valid()`

For batches:

```python
is_batch_valid(records)
```

returns a simple boolean.

This is useful for pipeline gates such as:

```text
Collect
  ↓
Parse
  ↓
Validate
  ↓
Continue only if valid
```

---

# `filter_valid()`

The validator provides:

```python
filter_valid(records)
```

which returns only valid records.

The source records are not modified.

---

# `filter_invalid()`

The complementary method:

```python
filter_invalid(records)
```

returns records that fail validation.

This is useful for:

* Debugging.
* Data-quality reports.
* Quarantine workflows.
* Historical data cleanup.

---

# Convenience Functions

The module also provides:

```python
validate_record()
```

```python
validate_records()
```

```python
is_valid_record()
```

These allow validation without explicitly creating a validator object.

---

# Validation Flow

A single record follows:

```text
LongShortRatioRecord
        │
        ├── Symbol
        │
        ├── Period
        │
        ├── Timestamp
        │
        ├── Long Account
        │
        ├── Short Account
        │
        ├── Long/Short Ratio
        │
        └── Ratio Consistency
                │
                ↓
        ValidationResult
```

---

# Batch Flow

A batch follows:

```text
Records
   │
   ├── Record Validation
   │
   ├── Duplicate Detection
   │
   ├── Timestamp Ordering
   │
   └── Batch Result
          │
          ├── total_records
          ├── valid_records
          ├── invalid_records
          └── errors
```

---

# Parser and Validator Relationship

`parser.py` and `validator.py` have intentionally different responsibilities.

### Parser

```text
Raw API
   ↓
Normalize
```

### Validator

```text
Normalized Record
   ↓
Check Quality
```

For example:

```text
"0.603"
```

becomes:

```text
0.603
```

in the parser.

Then the validator checks whether:

```text
0.603
```

is a valid finite numeric value.

---

# Validator and Analytics Relationship

The validator does not calculate trading analytics.

It does not calculate:

```text
long/short momentum
ratio change
ratio moving average
positioning extremes
positioning divergence
positioning acceleration
```

Those belong to the Indicators Analytics layer.

---

# Validator and Dataset Generator

The intended flow is:

```text
Raw Data
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
```

The validator therefore acts as a **data-quality gate** before downstream dataset creation.

---

# Validator and ML Models

The validator does not know whether the data will eventually be used by:

```text
LSTM
GRU
XGBoost
LightGBM
CatBoost
Transformer
TFT
```

Its job is simply to ensure that the normalized source data meets the configured quality requirements.

---

# Validator and Risk Engine

The validator must not be confused with the trading risk engine.

### Data Validator

```text
Is the market data valid?
```

### Risk Engine

```text
Can this trade be taken?
```

The data validator can reject a **data record**.

The risk engine can reject a **trade**.

These are fundamentally different responsibilities.

---

# Example Valid Record

Conceptually:

```text
symbol            = ETHUSDT
period            = 5m
timestamp         = 1754397000000
long_account      = 0.603
short_account     = 0.397
long_short_ratio  = 1.519
```

Assuming the ratio is within the configured tolerance of:

```text
0.603 / 0.397
```

the record can pass validation.

---

# Example Invalid Record

```text
symbol            = BTCUSDT
period            = invalid
timestamp         = -1
long_account      = -0.4
short_account     = NaN
long_short_ratio  = -2.0
```

Multiple validation errors should be reported instead of hiding the complete quality problem.

---

# Configuration Separation

The validation rules are kept in:

```python
LongShortRatioValidationConfig
```

rather than hard-coded throughout the validator.

This allows the pipeline to change policy without rewriting validation logic.

For example:

```text
Default
    ↓
ETHUSDT
    ↓
5m / 15m / 30m / 1h / ...
```

can be replaced with another explicitly configured policy when necessary.

---

# Data Quality Gate

The validator can act as a gate:

```text
                ┌───────────────┐
                │ Raw Exchange  │
                │     Data      │
                └───────┬───────┘
                        ↓
                ┌───────────────┐
                │    Parser     │
                └───────┬───────┘
                        ↓
                ┌───────────────┐
                │   Validator   │
                └───────┬───────┘
                        ↓
                ┌───────────────┐
                │ Valid Records │
                └───────┬───────┘
                        ↓
              Indicators Analytics
```

Invalid records can be routed to a data-quality or quarantine workflow rather than entering the model pipeline.

---

# Testing

Recommended test location:

```text
D:\Sachin Chakrawarti\eth_bot\
tests\
└── collectors\
    └── long_short_ratio\
        └── test_validator.py
```

Recommended tests include:

```text
valid record
invalid record type
invalid symbol
wrong symbol
empty symbol
invalid period
unsupported period
invalid timestamp
zero timestamp
negative timestamp
negative long account
negative short account
negative ratio
NaN values
Infinity values
boolean numeric values
inconsistent ratio
ratio tolerance
zero short account
duplicate timestamps
non-monotonic timestamps
empty batch
mixed valid/invalid batch
filter_valid
filter_invalid
strict validation behavior
configuration validation
```

---

# Important Design Rule

The validator should **not mutate records**.

It should inspect:

```text
LongShortRatioRecord
```

and return:

```text
ValidationResult
```

or:

```text
BatchValidationResult
```

This makes validation deterministic and easier to test.

---

# Position in the ETH Bot

The long/short ratio validator belongs to the **data ingestion and quality layer**, not the strategy or risk layer.

```text
Data Sources
    ↓
Collectors
    ↓
Parsers
    ↓
Validators
    ↓
Raw / Processed Storage
    ↓
Indicators Analytics
    ↓
Dataset Generation
    ↓
ML / DL Models
    ↓
Strategy Engine
    ↓
Risk Engine
    ↓
Execution Engine
```

---

# Final Responsibility

`long_short_ratio/validator.py` has one core responsibility:

> **Validate normalized ETH futures long/short ratio records for structural, type, numeric, timestamp, symbol, period, and consistency requirements before the data is allowed to proceed into downstream processing.**

It is a **data-quality component**, not a trading decision component.
