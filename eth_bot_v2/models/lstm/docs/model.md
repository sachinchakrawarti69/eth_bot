# LSTM Model Documentation

## Overview

The LSTM (Long Short-Term Memory) model is the primary deep learning model used for time-series forecasting in the Ethereum Trading Bot.

Its purpose is to learn temporal relationships from historical market data and generate predictions that support automated trading decisions.

---

# Model Objectives

The model is designed to:

* Predict future Ethereum prices
* Predict market direction
* Estimate future volatility
* Generate Buy/Hold/Sell signals
* Provide confidence scores
* Support risk management
* Improve trading strategies

---

# Why LSTM?

Financial markets are sequential by nature. The current market state depends on previous candles, trends, volatility, sentiment, and liquidity.

Unlike a standard feed-forward neural network, an LSTM is designed to remember important information across long sequences while forgetting irrelevant information.

Advantages include:

* Handles sequential data
* Learns long-term dependencies
* Reduces the vanishing gradient problem
* Suitable for financial time series
* Works well with multiple input features

---

# Model Architecture

```text
                    Input Features
                          │
                          ▼
                 Sequence Generator
                          │
                          ▼
                LSTM Layer (128 Units)
                          │
                          ▼
                    Dropout (0.20)
                          │
                          ▼
                 LSTM Layer (64 Units)
                          │
                          ▼
                    Dropout (0.20)
                          │
                          ▼
                   Dense Layer (32)
                          │
                          ▼
                    Output Layer
```

---

# Input Features

The model can consume features from multiple datasets.

## Price Data

* Open
* High
* Low
* Close
* Volume

---

## Order Book

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
* Greeks
* Implied Volatility

---

## Sentiment

* News Features
* Fear & Greed Index
* Whale Activity

---

## Blockchain

* Market Cap
* Supply
* Trading Volume
* On-chain Metrics

---

## Technical Indicators

Examples include:

* SMA
* EMA
* RSI
* MACD
* ATR
* ADX
* VWAP
* Bollinger Bands
* OBV
* Momentum
* ROC
* Stochastic RSI

---

# Input Shape

The model receives a three-dimensional tensor.

```text
(samples, sequence_length, features)
```

Example

```text
(10000, 60, 40)
```

Meaning

* 10,000 sequences
* 60 historical candles
* 40 engineered features

---

# Output Types

## Regression

Predicts:

* Next Close Price
* Next High
* Next Low

---

## Classification

Predicts:

* Buy
* Hold
* Sell

---

## Probability

Outputs may include:

* Probability of Price Increase
* Probability of Price Decrease
* Confidence Score

---

# Model Layers

## Input Layer

Receives the sequential feature matrix.

---

## LSTM Layer

Learns temporal patterns across historical market data.

Example

```text
Units: 128
Activation: tanh
```

---

## Dropout

Randomly disables neurons during training to reduce overfitting.

Example

```text
Rate: 0.20
```

---

## Dense Layer

Combines information extracted by the LSTM layers.

Example

```text
Units: 32
Activation: ReLU
```

---

## Output Layer

Depends on the prediction task.

Regression

```text
Dense(1)
```

Classification

```text
Dense(3)
Softmax
```

---

# Loss Functions

Regression

* Mean Squared Error (MSE)
* Mean Absolute Error (MAE)
* Huber Loss

Classification

* Cross Entropy Loss

---

# Optimizers

Supported optimizers include:

* Adam
* AdamW
* RMSprop
* SGD

Recommended default:

```text
Adam
Learning Rate = 0.001
```

---

# Hyperparameters

Typical starting values:

| Parameter        | Value |
| ---------------- | ----: |
| Sequence Length  |    60 |
| Batch Size       |    32 |
| Epochs           |   100 |
| Learning Rate    | 0.001 |
| Hidden Units     |   128 |
| Dropout          |  0.20 |
| Validation Split |   15% |

These values should be tuned for your dataset rather than treated as fixed.

---

# Training Workflow

```text
Historical Data
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
Train Model
        │
        ▼
Validate
        │
        ▼
Save Best Model
```

---

# Evaluation Metrics

## Regression

* MAE
* MSE
* RMSE
* MAPE
* R²

---

## Classification

* Accuracy
* Precision
* Recall
* F1 Score

---

## Trading Metrics

* Win Rate
* Profit Factor
* Sharpe Ratio
* Maximum Drawdown
* Total Return

---

# Model Files

```text
models/

├── lstm_model.py
├── stacked_lstm.py
├── bidirectional_lstm.py
├── attention_lstm.py
└── layers.py
```

---

# Checkpoints

```text
checkpoints/

├── best_model.pt
├── latest_model.pt
└── history/
```

The checkpoint with the best validation performance is typically used for inference.

---

# Inference

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
Load Model
        │
        ▼
Prediction
        │
        ▼
Trading Signal
```

---

# Limitations

Important considerations:

* Performance depends on data quality.
* Market conditions change over time.
* Historical performance does not guarantee future results.
* Regular retraining may be required.
* Predictions should be evaluated alongside risk management rules.

---

# Future Improvements

Planned enhancements include:

* Stacked LSTM
* Bidirectional LSTM
* Attention Mechanism
* Transformer Hybrid
* Multi-Timeframe Models
* Ensemble Models
* Probabilistic Forecasting
* Online Learning

---

# Integration

The LSTM model integrates with:

```text
SQLite Database
        │
        ▼
Data Collection
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
Signal Generation
        │
        ▼
Risk Management
        │
        ▼
Order Execution
```

---

# Summary

The LSTM model is the forecasting component of the Ethereum Trading Bot. It processes sequential market, derivatives, sentiment, and on-chain data to estimate future market behavior. Its modular design allows the preprocessing pipeline, training process, evaluation, and inference to evolve independently, making it straightforward to extend the system with additional architectures such as GRUs, Transformers, or ensemble models while reusing the same data pipeline.
