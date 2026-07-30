# Inference Documentation

## Overview

Inference is the process of using a trained LSTM model to generate predictions from new market data. Unlike training, inference does not update model weights. Instead, it loads a previously trained model, prepares the latest market data, and produces predictions that can be used by the trading system.

---

# Inference Pipeline

```text
                   Live Market Data
                           │
                           ▼
                 Load Latest Records
                           │
                           ▼
                  Data Validation
                           │
                           ▼
                 Feature Engineering
                           │
                           ▼
                   Technical Indicators
                           │
                           ▼
                    Data Normalization
                           │
                           ▼
                  Sequence Generation
                           │
                           ▼
                Load Trained LSTM Model
                           │
                           ▼
                    Run Model Inference
                           │
                           ▼
                  Post-process Prediction
                           │
                           ▼
                Trading Signal Generation
                           │
                           ▼
                  Store / Display Result
```

---

# Input Data

The inference pipeline may use the following data sources:

## Market Data

* OHLCV
* Order Book
* Trades

## Derivatives

* Funding Rate
* Open Interest
* Option Chain
* Greeks
* Implied Volatility

## Sentiment

* News
* Fear & Greed Index
* Whale Activity

## Blockchain

* On-chain Metrics

---

# Input Shape

The LSTM expects sequential input.

Example

```text
(samples, sequence_length, features)
```

Typical example

```text
(1, 60, 40)
```

Meaning

* 1 prediction sample
* 60 historical candles
* 40 engineered features

---

# Data Preparation

Before inference, the system performs:

* Load latest market records
* Merge multiple datasets
* Remove invalid values
* Handle missing values
* Compute technical indicators
* Normalize features using the saved scaler
* Create the final input sequence

---

# Model Loading

The inference engine loads the best trained checkpoint.

Example

```text
checkpoints/
├── best_model.pt
└── latest_model.pt
```

Only trained models are used during inference.

---

# Prediction Types

The model can generate one or more outputs.

## Regression

* Next Close Price
* Next High
* Next Low

## Classification

* Buy
* Hold
* Sell

## Probability

* Probability of Price Increase
* Probability of Price Decrease

## Risk

* Confidence Score
* Expected Volatility
* Estimated Risk Level

---

# Example Workflow

```text
Last 60 ETH Candles
          │
          ▼
Feature Engineering
          │
          ▼
Normalization
          │
          ▼
Sequence Creation
          │
          ▼
LSTM Prediction
          │
          ▼
Predicted Close Price
          │
          ▼
Buy / Hold / Sell Signal
```

---

# Post-processing

Predictions are converted into useful trading information.

Examples:

* Reverse normalization
* Calculate expected return
* Determine market direction
* Calculate confidence score
* Generate trading signal

---

# Trading Signals

Example rules

```text
Expected Return > 2%
AND

Confidence > 85%

↓

BUY
```

```text
Expected Return between -2% and 2%

↓

HOLD
```

```text
Expected Return < -2%

↓

SELL
```

These thresholds are examples and should be validated through backtesting.

---

# Inference Frequency

| Data Type | Typical Frequency |
| --------- | ----------------- |
| 1 Minute  | Every minute      |
| 5 Minute  | Every 5 minutes   |
| 15 Minute | Every 15 minutes  |
| 1 Hour    | Every hour        |
| 4 Hour    | Every 4 hours     |
| 1 Day     | Daily             |

---

# Real-Time Inference

```text
Exchange API
      │
      ▼
Receive Latest Candle
      │
      ▼
Update Indicators
      │
      ▼
Prepare Sequence
      │
      ▼
Run LSTM
      │
      ▼
Prediction
      │
      ▼
Trading Decision
```

---

# Output Example

```text
Prediction Time

2026-08-01 12:00 UTC

Current Price

3852.40

Predicted Close

3884.75

Expected Change

+0.84%

Confidence

91.6%

Signal

BUY
```

---

# Saving Predictions

Predictions may be stored in the database.

Example table

```text
predictions

├── prediction_time
├── current_price
├── predicted_price
├── predicted_direction
├── confidence
├── signal
└── model_version
```

---

# Performance Considerations

For efficient inference:

* Load the model once and reuse it.
* Cache reusable resources.
* Reuse the fitted scaler.
* Validate input dimensions.
* Avoid unnecessary database queries.
* Log inference time and errors.

---

# Error Handling

The inference pipeline should detect:

* Missing model files
* Missing scaler
* Invalid input dimensions
* Missing required features
* Corrupted checkpoints
* Database connection failures
* API failures
* Empty datasets

---

# Monitoring

Track the following metrics:

* Inference latency
* Prediction success rate
* Model confidence
* Prediction accuracy
* Signal distribution
* Prediction history

---

# Integration

The inference engine integrates with:

```text
SQLite Database
        │
        ▼
Feature Engineering
        │
        ▼
LSTM Model
        │
        ▼
Prediction Engine
        │
        ▼
Risk Management
        │
        ▼
Trading Strategy
        │
        ▼
Order Execution
```

---

# Future Enhancements

Future versions may include:

* Ensemble inference
* Multi-timeframe predictions
* Attention-based LSTM
* Transformer integration
* Online model updates
* GPU inference
* Batch prediction
* Reinforcement learning integration

---

# Summary

The inference pipeline transforms live Ethereum market data into actionable predictions by applying the same preprocessing used during training, running a trained LSTM model, and converting the results into trading signals. Consistent preprocessing, reliable model loading, and robust monitoring help ensure accurate and repeatable predictions in both paper trading and live trading environments.
