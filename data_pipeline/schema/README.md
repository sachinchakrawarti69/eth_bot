# Data Pipeline - Schema

## Overview

The **Schema** module defines the structure of every dataset that flows through the Data Pipeline.

A schema specifies:

- Required fields
- Data types
- Validation rules
- Constraints
- Default values
- Metadata

Every stage of the pipeline has its own schema to ensure data consistency and reliability.

---

# Why Schemas?

Market data comes from many different sources.

Examples:

- Binance
- Bybit
- OKX
- News APIs
- On-chain APIs
- Fear & Greed Index
- Whale trackers

Each source returns data in a different format.

The Schema module standardizes all data before it enters the rest of the pipeline.

---

# Pipeline Position

```
Exchange APIs
        │
        ▼
Collectors
        │
        ▼
Raw Schema
        │
        ▼
Validation
        │
        ▼
Processing
        │
        ▼
Processed Schema
        │
        ▼
Technical Indicators
        │
        ▼
Indicator Schema
        │
        ▼
Feature Engineering
        │
        ▼
Feature Schema
        │
        ▼
Dataset Builder
        │
        ▼
Dataset Schema
        │
        ▼
AI Models
```

---

# Directory Structure

```text
schema/
│
├── README.md
│
├── raw/
│   ├── ohlcv.py
│   ├── trades.py
│   ├── orderbook.py
│   ├── funding_rate.py
│   ├── open_interest.py
│   ├── liquidations.py
│   ├── long_short_ratio.py
│   ├── option_chain.py
│   ├── greeks.py
│   ├── implied_volatility.py
│   ├── fear_greed.py
│   ├── whales.py
│   ├── news.py
│   └── onchain.py
│
├── processed/
│   ├── market_data.py
│   ├── derivatives.py
│   ├── sentiment.py
│   ├── onchain.py
│   └── merged_dataset.py
│
├── indicators/
│   ├── trend.py
│   ├── momentum.py
│   ├── volatility.py
│   ├── volume.py
│   └── custom.py
│
├── features/
│   ├── price_features.py
│   ├── volume_features.py
│   ├── derivative_features.py
│   ├── orderbook_features.py
│   ├── sentiment_features.py
│   ├── onchain_features.py
│   └── time_features.py
│
├── datasets/
│   ├── lstm.py
│   ├── xgboost.py
│   ├── lightgbm.py
│   ├── transformer.py
│   └── tft.py
│
└── common.py
```

---

# Schema Stages

## 1. Raw Schema

Represents data exactly as received from external sources.

Examples:

- OHLCV
- Trades
- Order Book
- Funding Rate
- Open Interest
- Liquidations

Example:

```
Exchange

↓

Raw JSON

↓

Raw Schema
```

No calculations are performed.

Only formatting and validation.

---

## 2. Processed Schema

Represents cleaned and standardized market data.

Processing includes:

- Timestamp alignment
- Duplicate removal
- Type conversion
- Missing value handling
- Data merging
- Timeframe alignment

Example:

```
Raw Data

↓

Processing

↓

Processed Schema
```

---

## 3. Indicator Schema

Represents outputs from technical indicators.

Examples:

- RSI
- MACD
- EMA
- SMA
- Bollinger Bands
- ATR
- ADX
- VWAP

Example:

```
Processed Data

↓

Indicators

↓

Indicator Schema
```

---

## 4. Feature Schema

Represents engineered features used by AI models.

Examples:

- Price returns
- Log returns
- Rolling statistics
- Volatility features
- Order book imbalance
- Funding features
- Open interest features
- Time features

Example:

```
Indicators

↓

Feature Engineering

↓

Feature Schema
```

---

## 5. Dataset Schema

Represents the final datasets consumed by AI models.

Different models require different formats.

Examples:

- LSTM sequences
- XGBoost tables
- LightGBM tables
- TFT sequences
- Transformer datasets

Example:

```
Feature Matrix

↓

Dataset Builder

↓

Dataset Schema
```

---

# Validation Responsibilities

Every schema should validate:

- Required fields
- Data types
- Missing values
- Allowed ranges
- Timestamp format
- Duplicate keys
- Field consistency

---

# Schema Evolution

Data becomes richer as it moves through the pipeline.

```
Raw Data

↓

Processed Data

↓

Indicators

↓

Features

↓

Datasets
```

Each stage adds information while preserving consistency.

---

# Benefits

Using schemas provides:

- Consistent data structure
- Strong validation
- Easier debugging
- Better maintainability
- Safer data transformations
- Reusable validation logic
- Model compatibility
- Reliable AI training

---

# Design Principles

Every schema should be:

- Explicit
- Versionable
- Reusable
- Easy to validate
- Independent of data source
- Independent of AI model
- Easy to extend

---

# Future Enhancements

Potential additions include:

- Schema versioning
- Automatic schema migration
- JSON Schema export
- Avro support
- Protocol Buffers
- Pydantic models
- Great Expectations integration
- Data lineage tracking

---

# Summary

The Schema module defines the contract for every stage of the data pipeline.

```
Raw Data
      ↓
Raw Schema
      ↓
Processed Schema
      ↓
Indicator Schema
      ↓
Feature Schema
      ↓
Dataset Schema
      ↓
AI Models
```

By validating data at every stage, the pipeline remains reliable, maintainable, and ready for machine learning and production trading.