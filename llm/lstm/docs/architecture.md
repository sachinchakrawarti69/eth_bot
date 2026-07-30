# LSTM Architecture

## Overview

The LSTM (Long Short-Term Memory) architecture is the core deep learning model used in the Ethereum Trading Bot. It is designed to learn temporal patterns from historical market data and generate predictions for future market behavior.

Unlike traditional machine learning models, LSTMs can capture long-term dependencies in sequential financial data, making them well-suited for time-series forecasting.

---

# High-Level Architecture

```text
                         Ethereum Trading Bot

┌──────────────────────────────────────────────────────────────┐
│                     Data Collection Layer                    │
├──────────────────────────────────────────────────────────────┤
│ OHLCV                                                       │
│ Order Book                                                  │
│ Trades                                                      │
│ Funding Rate                                                │
│ Open Interest                                               │
│ Option Chain                                                │
│ Greeks                                                      │
│ Implied Volatility                                          │
│ News                                                        │
│ On-chain Data                                               │
│ Fear & Greed                                                │
│ Whale Transactions                                          │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    Data Storage Layer                        │
├──────────────────────────────────────────────────────────────┤
│ SQLite (ETH.db)                                              │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                  Data Preprocessing Layer                    │
├──────────────────────────────────────────────────────────────┤
│ Data Cleaning                                                │
│ Missing Value Handling                                       │
│ Feature Engineering                                          │
│ Technical Indicators                                         │
│ Scaling & Normalization                                      │
│ Sequence Generation                                          │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                       LSTM Model                             │
├──────────────────────────────────────────────────────────────┤
│ Input Layer                                                  │
│ LSTM Layer(s)                                                │
│ Dropout                                                      │
│ Dense Layer                                                  │
│ Output Layer                                                 │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    Prediction Layer                          │
├──────────────────────────────────────────────────────────────┤
│ Price Prediction                                             │
│ Direction Prediction                                         │
│ Buy / Hold / Sell Signal                                    │
│ Confidence Score                                             │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                 Backtesting & Evaluation                     │
├──────────────────────────────────────────────────────────────┤
│ Strategy Testing                                             │
│ Performance Metrics                                          │
│ Risk Analysis                                                │
└──────────────────────────────────────────────────────────────┘
```

---

# Data Flow

```text
Market APIs
      │
      ▼
Database (ETH.db)
      │
      ▼
Load Historical Data
      │
      ▼
Clean Data
      │
      ▼
Feature Engineering
      │
      ▼
Technical Indicators
      │
      ▼
Normalization
      │
      ▼
Sequence Creation
      │
      ▼
LSTM Training
      │
      ▼
Model Evaluation
      │
      ▼
Prediction
      │
      ▼
Trading Decision
```

---

# Input Features

The LSTM receives multiple categories of features.

## Price Features

* Open
* High
* Low
* Close
* Volume

---

## Market Structure

* Bid Price
* Ask Price
* Bid Volume
* Ask Volume
* Spread

---

## Derivatives

* Funding Rate
* Open Interest
* Option Chain
* Implied Volatility
* Greeks

---

## Technical Indicators

* SMA
* EMA
* RSI
* MACD
* ATR
* ADX
* Bollinger Bands
* VWAP
* OBV
* Momentum

---

## Sentiment

* Fear & Greed Index
* News Sentiment
* Whale Activity

---

## On-chain Metrics

* Market Cap
* Circulating Supply
* Total Supply
* Trading Volume
* ATH
* ATL

---

# Sequence Generation

Example:

```text
60 Historical Candles
        │
        ▼
Sequence
        │
        ▼
Predict Candle 61
```

For every prediction:

```
Input Shape

(samples, sequence_length, features)

Example

(5000, 60, 30)
```

Where:

* 5000 = training samples
* 60 = candles per sequence
* 30 = engineered features

---

# LSTM Network

```text
Input Layer
      │
      ▼
LSTM Layer (128 Units)
      │
      ▼
Dropout (0.2)
      │
      ▼
LSTM Layer (64 Units)
      │
      ▼
Dropout (0.2)
      │
      ▼
Dense Layer (32)
      │
      ▼
Output Layer
```

---

# Training Pipeline

```text
Historical Data
        │
        ▼
Train Dataset
        │
        ▼
Validation Dataset
        │
        ▼
Model Training
        │
        ▼
Checkpoint Saving
        │
        ▼
Performance Evaluation
        │
        ▼
Best Model
```

---

# Model Outputs

The network can predict:

* Next Closing Price
* Future Price Direction
* Buy Probability
* Sell Probability
* Hold Probability
* Confidence Score
* Expected Volatility

---

# Evaluation

Regression Metrics

* MAE
* MSE
* RMSE
* MAPE
* R² Score

Classification Metrics

* Accuracy
* Precision
* Recall
* F1 Score

Trading Metrics

* Win Rate
* Profit Factor
* Sharpe Ratio
* Maximum Drawdown
* Annual Return

---

# Checkpoint System

During training:

```text
Epoch

↓

Validation Loss

↓

Best Model?

↓

Yes

↓

Save Checkpoint
```

Files:

```
checkpoints/

best_model.pt

latest_model.pt
```

---

# Prediction Pipeline

```text
Latest Market Data
        │
        ▼
Feature Engineering
        │
        ▼
Normalization
        │
        ▼
Create Sequence
        │
        ▼
Load Trained Model
        │
        ▼
Run Inference
        │
        ▼
Prediction
        │
        ▼
Trading Signal
```

---

# Future Extensions

The architecture is designed to support additional models and workflows without changing the data pipeline.

Future additions include:

* GRU
* Transformer
* Temporal Fusion Transformer
* XGBoost
* LightGBM
* CatBoost
* Random Forest
* Ensemble Learning
* Reinforcement Learning Agents

---

# Design Principles

* Modular components
* Reusable preprocessing
* Separate training and inference
* Configurable hyperparameters
* Scalable to multiple models
* Easy experiment tracking
* Reproducible workflows
* Production-ready deployment

---

# Summary

The LSTM architecture provides a complete machine learning pipeline for Ethereum market prediction. By combining historical prices, derivatives data, technical indicators, sentiment, and on-chain metrics, the model can generate informed predictions and trading signals while remaining extensible for future AI models and strategies.
