# Option Chain Validator

## Overview

`option_chain/validator.py` validates normalized option-chain records produced by `option_chain/parser.py`.

Its responsibility is **data-quality validation**.

```text
Exchange API
     ↓
collector.py
     ↓
Raw Response
     ↓
parser.py
     ↓
OptionChainRecord
     ↓
validator.py
     ↓
Validated Option Data
```

The validator does not parse raw exchange responses and does not make trading decisions.

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

The validator checks:

* Symbol validity.
* Option type.
* Strike price.
* Expiration timestamp.
* Bid price.
* Ask price.
* Mark price.
* Last price.
* Underlying price.
* Bid quantity.
* Ask quantity.
* Volume.
* Open interest.
* Record timestamp.
* Basic market-data relationships.
* Basic temporal consistency.

---

# Non-Responsibilities

The validator does **not**:

* Make API requests.
* Retry requests.
* Parse raw JSON.
* Calculate Greeks.
* Calculate implied volatility.
* Generate indicators.
* Generate ML features.
* Generate trading signals.
* Approve trades.
* Reject trades for trading-risk reasons.
* Execute orders.

The distinction is:

```text
Validator
    ↓
"Is this market data structurally valid?"

Risk Engine
    ↓
"Should this trade be allowed?"
```

These are fundamentally different responsibilities.

---

# Main Class

The main validation class is:

```python
OptionChainValidator
```

It validates instances of:

```python
OptionChainRecord
```

from:

```text
option_chain/parser.py
```

---

# Validation Result

The validator returns:

```python
ValidationResult
```

with:

```text
valid
errors
```

Example:

```python
ValidationResult(
    valid=True,
    errors=(),
)
```

An invalid record may produce:

```python
ValidationResult(
    valid=False,
    errors=(
        "bid_price cannot be greater than ask_price",
    ),
)
```

---

# Validation Error

The module defines:

```python
OptionChainValidationError
```

This is raised by:

```python
validate_or_raise()
```

when a record fails validation.

---

# Validation Flow

```text
OptionChainRecord
       ↓
Validate Symbol
       ↓
Validate Option Type
       ↓
Validate Strike
       ↓
Validate Expiry
       ↓
Validate Prices
       ↓
Validate Quantities
       ↓
Validate Market Relationships
       ↓
Validate Timestamp
       ↓
Validate Temporal Relationships
       ↓
ValidationResult
```

---

# Symbol Validation

The validator requires the symbol to be a string.

It must:

* Exist.
* Not be empty.
* Not contain leading whitespace.
* Not contain trailing whitespace.
* Be uppercase.

Valid:

```text
ETH-26AUG-3500-C
```

Invalid:

```text
eth-26aug-3500-c
```

Invalid:

```text
 ETH-26AUG-3500-C
```

Invalid:

```text
ETH-26AUG-3500-C 
```

Invalid:

```text
""
```

---

# Option Type Validation

Only normalized option types are accepted:

```text
CALL
PUT
```

For example:

```text
CALL → valid
PUT  → valid
```

while:

```text
C
P
call
put
```

should normally already have been normalized by the parser.

The validator operates on the normalized representation.

---

# Strike Price Validation

`strike_price` must be:

* Numeric.
* Finite.
* Greater than zero.
* Not boolean.

Valid:

```text
3500.0
```

Invalid:

```text
0
```

Invalid:

```text
-100
```

Invalid:

```text
NaN
```

Invalid:

```text
Infinity
```

---

# Why Strike Must Be Positive

An option strike represents the contractual exercise price.

A non-positive strike is not considered valid option-chain market data for this collector.

---

# Expiration Validation

`expiry_timestamp` must:

* Be an integer.
* Not be boolean.
* Fall within the supported timestamp range.

The configured range is:

```text
2000-01-01
        ↓
2100-01-01
```

represented as Unix milliseconds.

This catches obvious timestamp corruption.

---

# Why Timestamp Range Validation Exists

A malformed timestamp such as:

```text
123
```

could otherwise be interpreted as a valid Unix timestamp while representing a completely unrealistic option expiration.

Range validation catches these errors early.

---

# Price Validation

The validator checks:

```text
bid_price
ask_price
mark_price
last_price
underlying_price
```

Each optional price must be:

* Numeric.
* Finite.
* Non-negative.

`None` is allowed because these fields are optional.

---

# Valid Price Examples

```text
0
1.25
120.50
3500.00
```

---

# Invalid Price Examples

```text
-1
NaN
Infinity
-Infinity
True
False
```

---

# Why Zero Price Is Allowed

A zero price may represent an option with no current quoted/traded value.

Therefore:

```text
price = 0
```

is structurally different from:

```text
price = -1
```

The validator permits zero but rejects negative values.

---

# Quantity Validation

The validator checks:

```text
bid_quantity
ask_quantity
volume
open_interest
```

Each must be:

* Numeric.
* Finite.
* Non-negative.

Missing values are allowed.

---

# Quantity Examples

Valid:

```text
0
10
1000.5
```

Invalid:

```text
-10
NaN
Infinity
```

---

# Open Interest

`open_interest` must be non-negative.

For example:

```text
open_interest = 12500
```

is valid.

But:

```text
open_interest = -100
```

is invalid.

The validator does not determine whether the open interest is unusually high or low.

That is an analytics concern.

---

# Volume

`volume` must be non-negative.

The validator does not decide whether volume is:

```text
high
low
unusual
abnormal
```

It only checks whether the value is structurally acceptable.

---

# Bid Price vs Ask Price

The validator enforces:

```text
bid_price <= ask_price
```

when both values are available.

For example:

```text
bid = 120
ask = 125
```

is valid.

But:

```text
bid = 130
ask = 125
```

is invalid.

---

# Why Bid/Ask Consistency Matters

A crossed market:

```text
bid > ask
```

can indicate:

* Corrupted data.
* Incorrect field mapping.
* Stale records.
* Exchange/API inconsistency.
* Timestamp mismatch.

It should therefore be detected before downstream analytics.

---

# Mark Price Validation

When:

```text
bid_price
ask_price
mark_price
```

are all available, the validator expects:

```text
bid_price <= mark_price <= ask_price
```

For example:

```text
bid  = 120
mark = 122
ask  = 125
```

is valid.

---

# Invalid Mark Price

For example:

```text
bid  = 120
mark = 140
ask  = 125
```

is invalid because:

```text
mark > ask
```

---

# Missing Market Fields

The validator allows missing optional fields.

For example:

```text
bid_price = None
ask_price = None
mark_price = None
```

does not automatically invalidate the record.

This is intentional because exchange data can be incomplete.

---

# Timestamp Validation

The optional:

```text
timestamp
```

must be:

* An integer.
* Not boolean.
* Within the supported timestamp range.

If it is absent:

```text
timestamp = None
```

the record can still be valid.

---

# Expiry vs Record Timestamp

The validator checks:

```text
expiry_timestamp >= timestamp
```

when both timestamps exist.

An option cannot have an expiration timestamp earlier than the timestamp at which the market record was observed.

---

# Example

Valid:

```text
record timestamp:
2026-08-05

expiry:
2026-08-28
```

Invalid:

```text
record timestamp:
2026-08-28

expiry:
2026-08-05
```

---

# Why Temporal Validation Matters

Timestamp corruption can otherwise produce serious downstream problems.

For example:

```text
expiry - current_time
```

is used to determine time to expiration.

If timestamps are wrong, downstream calculations such as:

```text
time to expiry
implied volatility
option pricing
term structure
```

can become invalid.

---

# Generic Numeric Validation

The validator uses two important numeric validation patterns.

### Required positive number

Used for:

```text
strike_price
```

The value must be:

```text
finite
and
> 0
```

### Optional non-negative number

Used for:

```text
bid_price
ask_price
mark_price
last_price
underlying_price
bid_quantity
ask_quantity
volume
open_interest
```

The value may be:

```text
None
```

or:

```text
finite and >= 0
```

---

# Boolean Protection

Python treats:

```python
True
False
```

as subclasses of integers.

The validator therefore explicitly rejects booleans.

For example:

```python
strike_price=True
```

must not become:

```text
1
```

Similarly:

```python
volume=False
```

must not become:

```text
0
```

This prevents silent schema corruption.

---

# Finite Number Validation

The validator rejects:

```text
NaN
Infinity
-Infinity
```

because these values can contaminate downstream calculations.

For example:

```text
NaN
```

could propagate into:

```text
IV
Greeks
features
models
signals
```

and make the resulting data unreliable.

---

# `validate()`

The primary method is:

```python
validate(record)
```

It returns:

```python
ValidationResult
```

rather than immediately raising an exception.

This is useful when the pipeline wants to collect all validation problems.

---

# Example

Conceptually:

```python
result = validator.validate(record)

if result.valid:
    store(record)
else:
    log(result.errors)
```

---

# Multiple Errors

A single record can have multiple validation problems.

For example:

```text
symbol is not uppercase
bid_price is negative
ask_price is negative
expiry timestamp is invalid
```

The validator returns all detected errors instead of stopping at the first error.

This improves diagnostics.

---

# `validate_or_raise()`

The method:

```python
validate_or_raise(record)
```

is useful when invalid data should immediately stop the current operation.

Conceptually:

```python
validator.validate_or_raise(record)
```

If invalid:

```text
OptionChainValidationError
```

is raised.

---

# `is_valid()`

The method:

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

This is useful for simple filtering.

Example:

```python
valid_records = [
    record
    for record in records
    if validator.is_valid(record)
]
```

---

# `validate_many()`

The method:

```python
validate_many(records)
```

validates multiple records and returns a corresponding list of:

```text
ValidationResult
```

This preserves the relationship between each input record and its validation result.

---

# `filter_valid()`

The method:

```python
filter_valid(records)
```

returns only records that pass validation.

Conceptually:

```text
Records
   ↓
Validator
   ↓
Valid Records
```

---

# `filter_invalid()`

The method:

```python
filter_invalid(records)
```

returns only records that fail validation.

This is useful for:

* Debugging.
* Data-quality reports.
* Quarantine pipelines.
* Error analysis.

---

# Validation vs Parser

The parser performs:

```text
"3500"
   ↓
3500.0
```

The validator performs:

```text
3500.0
   ↓
Is it finite?
Is it positive?
```

Therefore:

```text
Parser
= normalization

Validator
= data-quality enforcement
```

---

# Validation vs Analytics

The validator asks:

```text
Is volume non-negative?
```

Analytics may ask:

```text
Is volume unusually high?
```

The validator asks:

```text
Is open interest numeric?
```

Analytics may ask:

```text
Is open interest increasing rapidly?
```

These should remain separate.

---

# Validation vs Risk Engine

The validator may reject:

```text
bid_price > ask_price
```

because the market-data record is inconsistent.

The risk engine may reject a trade because:

```text
position size too large
daily loss limit exceeded
portfolio exposure too high
```

These are not the same kind of rejection.

The architecture should remain:

```text
Data Validator
     ↓
Data Quality

Risk Engine
     ↓
Trade Risk
```

---

# Data Pipeline Position

The option-chain validator sits inside the collection pipeline:

```text
Data Source
    ↓
Collector
    ↓
Raw Storage
    ↓
Parser
    ↓
Validator
    ↓
Processed Storage
    ↓
Analytics
    ↓
Features
    ↓
Models
```

---

# Invalid Data Handling

The validator itself does not decide how invalid data should be stored.

The surrounding pipeline can choose to:

```text
Valid
  ↓
Processed Storage
```

and:

```text
Invalid
  ↓
Rejected / Quarantine Storage
```

For example:

```text
data_pipeline/
├── raw/
├── processed/
└── quarantine/
```

The validator should report the problem; pipeline orchestration decides what happens next.

---

# Suggested Quarantine Information

For rejected records, the pipeline should ideally preserve:

```text
record
validation errors
collector timestamp
source
symbol
parser version
validator version
```

This makes data-quality incidents traceable.

---

# Testing

Recommended test location:

```text
D:\Sachin Chakrawarti\eth_bot\
tests\
└── collectors\
    └── option_chain\
        └── test_validator.py
```

Recommended tests:

```text
valid CALL
valid PUT
empty symbol
lowercase symbol
symbol whitespace
invalid option type
zero strike
negative strike
NaN strike
infinite strike
invalid expiry
valid expiry
negative bid
negative ask
negative mark
negative volume
negative open interest
bid greater than ask
mark below bid
mark above ask
valid mark
missing optional values
invalid timestamp
expiry before timestamp
valid timestamp relationship
boolean numeric fields
multiple validation errors
validate_or_raise()
is_valid()
validate_many()
filter_valid()
filter_invalid()
```

---

# Example Valid Record

Conceptually:

```text
symbol:
ETH-26AUG-3500-C

option_type:
CALL

strike_price:
3500.0

expiry_timestamp:
valid future timestamp

bid_price:
120.0

ask_price:
125.0

mark_price:
122.5

volume:
100.0

open_interest:
2500.0
```

This should pass the structural and consistency checks.

---

# Example Invalid Record

Conceptually:

```text
symbol:
eth-26aug-3500-c

option_type:
CALL

strike_price:
-3500

bid_price:
130

ask_price:
120
```

Problems include:

```text
symbol is not uppercase
strike_price is negative
bid_price > ask_price
```

The validator should return all applicable errors.

---

# Important Design Principle

The validator follows:

> **Reject bad data, not trading opportunities.**

A record should be rejected when its data violates defined quality or consistency rules.

The validator should not reject data simply because:

```text
volume is low
open interest is low
spread is wide
volatility is high
price movement is bearish
```

Those are analytics or strategy considerations unless explicitly defined as data-integrity requirements.

---

# Relationship With Option Analytics

After validation:

```text
Validated Option Chain
        ↓
Option Analytics
        ├── Implied Volatility
        ├── Greeks
        ├── IV Surface
        ├── IV Term Structure
        ├── Put/Call Metrics
        └── Skew
```

This ensures downstream calculations begin with structurally reliable data.

---

# Relationship With ML Pipeline

Validated option-chain data can eventually feed:

```text
Option Features
       ↓
Dataset
       ↓
Training
       ↓
Validation
       ↓
Prediction
```

Potential features may include:

```text
implied volatility
IV rank
IV percentile
put/call open-interest ratio
volume imbalance
bid/ask spread
term structure
volatility skew
```

These are **not** generated by the validator.

---

# Final Responsibility

`option_chain/validator.py` has one core responsibility:

> **Validate normalized option-chain records for structural correctness, numeric integrity, timestamp consistency, and basic market-data relationships before the records enter downstream storage, analytics, feature engineering, and machine-learning pipelines.**
