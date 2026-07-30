# Dataset Documentation

## Overview

This document describes the datasets used by the LSTM model for the Ethereum Trading Bot.

The objective is to combine multiple sources of market information into a single machine learning dataset capable of predicting future Ethereum price movements, volatility, and trading signals.

---

# Dataset Architecture

```text
Market APIs
      │
      ▼
Raw Data Collection
      │
      ▼
SQLite Database (ETH.db)
      │
      ▼
Feature Engineering
      │
      ▼
ML Dataset
      │
      ▼
Train / Validation / Test
      │
      ▼
LSTM Model
```

---

# Data Sources

The model uses data collected from multiple sources.

## 1. OHLCV

Table

```text
ohlcv
```

Description

Historical candlestick data.

Columns

* Open Time
* Open
* High
* Low
* Close
* Volume
* Close Time
* Number of Trades
* Quote Asset Volume
* Taker Buy Volume

Purpose

Primary price information.

---

## 2. Order Book

Table

```text
orderbook
```

Description

Market depth snapshots.

Columns

* Best Bid
* Best Ask
* Bid Quantity
* Ask Quantity
* Spread

Purpose

Liquidity analysis.

---

## 3. Trades

Table

```text
trades
```

Description

Executed market trades.

Columns

* Price
* Quantity
* Trade Time
* Buyer Maker Flag

Purpose

Short-term market activity.

---

## 4. Funding Rate

Table

```text
funding_rate
```

Description

Perpetual futures funding information.

Columns

* Funding Rate
* Funding Time
* Mark Price

Purpose

Market sentiment from derivatives.

---

## 5. Open Interest

Table

```text
open_interest
```

Description

Open futures contracts.

Columns

* Open Interest
* Open Interest Value

Purpose

Measure leveraged market participation.

---

## 6. Option Chain

Table

```text
option_chain
```

Description

Ethereum options market.

Columns

* Strike
* Expiration
* Option Type
* Bid
* Ask
* Mark Price
* Volume
* Open Interest

Purpose

Options market analysis.

---

## 7. Greeks

Table

```text
greeks
```

Description

Option sensitivity metrics.

Columns

* Delta
* Gamma
* Theta
* Vega
* Rho

Purpose

Measure option risk.

---

## 8. Implied Volatility

Table

```text
implied_volatility
```

Description

Expected future volatility.

Columns

* Mark IV
* Bid IV
* Ask IV

Purpose

Volatility forecasting.

---

## 9. News

Table

```text
news
```

Description

Cryptocurrency news articles.

Columns

* Source
* Title
* Description
* Published Time
* URL

Purpose

News sentiment analysis.

---

## 10. On-chain

Table

```text
onchain
```

Description

Blockchain and market metrics.

Columns

* Market Cap
* Total Supply
* Circulating Supply
* Total Volume
* ATH
* ATL

Purpose

Network fundamentals.

---

## 11. Whale Activity

Table

```text
whales
```

Description

Large blockchain transactions.

Columns

* Transaction Hash
* Sender
* Receiver
* Amount
* Block Number

Purpose

Track large market participants.

---

## 12. Fear & Greed Index

Table

```text
fear_greed
```

Description

Overall crypto market sentiment.

Columns

* Value
* Classification
* Timestamp

Purpose

Market psychology.

---

# Feature Engineering

Raw data is transformed into model features.

Examples

* Price Returns
* Log Returns
* Rolling Mean
* Rolling Standard Deviation
* Price Momentum
* Volume Change
* Funding Change
* Open Interest Change
* Volatility
* Bid/Ask Spread
* Order Book Imbalance

---

# Technical Indicators

Generated indicators include:

Trend

* SMA
* EMA
* WMA
* HMA

Momentum

* RSI
* Stochastic RSI
* ROC
* Momentum

Trend Strength

* ADX
* DMI

Volatility

* ATR
* Bollinger Bands
* Keltner Channels

Volume

* VWAP
* OBV
* CMF
* MFI

Oscillators

* MACD
* Signal Line
* MACD Histogram

---

# Data Cleaning

The preprocessing pipeline performs:

* Duplicate removal
* Missing value handling
* Timestamp alignment
* Data type conversion
* Feature validation
* Outlier inspection

---

# Dataset Split

```text
Training      70%

Validation    15%

Testing       15%
```

Example

```text
100,000 Samples

↓

70,000 Train

15,000 Validation

15,000 Test
```

---

# Sequence Creation

The LSTM uses sequential input.

Example

```text
Previous 60 Candles

↓

Predict Candle 61
```

Input Shape

```text
(samples, sequence_length, features)
```

Example

```text
(50000, 60, 40)
```

Where

* Samples = 50,000
* Sequence Length = 60
* Features = 40

---

# Normalization

Supported methods

* Min-Max Scaling
* Standard Scaling
* Robust Scaling

The fitted scaler is saved for use during inference to ensure predictions use the same feature scaling as training.

---

# Labels

Regression

* Next Close Price
* Next High
* Next Low

Classification

* Buy
* Hold
* Sell

Binary

* Price Up
* Price Down

---

# Database

Primary database

```text
storage/
└── database/
    └── ETH.db
```

Processed datasets

```text
llm/
└── lstm/
    └── data/
        ├── raw/
        ├── processed/
        ├── features/
        ├── train/
        ├── validation/
        └── test/
```

---

# Data Refresh Strategy

| Dataset            | Typical Refresh        |
| ------------------ | ---------------------- |
| OHLCV              | Every candle           |
| Order Book         | Seconds                |
| Trades             | Seconds                |
| Funding Rate       | Every funding interval |
| Open Interest      | Minutes                |
| Option Chain       | Minutes                |
| Greeks             | Minutes                |
| Implied Volatility | Minutes                |
| News               | Every 5–15 minutes     |
| On-chain           | Hourly                 |
| Whale Activity     | Minutes                |
| Fear & Greed       | Daily                  |

---

# Data Quality Checks

Before training, verify:

* No duplicate timestamps
* No missing required columns
* Numeric fields are valid
* Chronological ordering
* Consistent feature dimensions
* No data leakage between training and testing

---

# Summary

The LSTM dataset combines market prices, derivatives, sentiment, on-chain metrics, and engineered technical indicators into a unified training dataset. A consistent preprocessing pipeline ensures reproducible training, evaluation, and inference while making it easy to extend the system with new data sources and models.
