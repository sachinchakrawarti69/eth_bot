# Training Documentation

## Overview

The training pipeline is responsible for building an LSTM model that learns patterns from historical Ethereum market data. During training, the model adjusts its internal parameters using labeled historical data to minimize prediction error.

The trained model is later used during inference to generate predictions and trading signals.

---

# Training Pipeline

```text
                 Historical Market Data
                          │
                          ▼
                 Load Data from ETH.db
                          │
                          ▼
                    Data Validation
                          │
                          ▼
                   Data Cleaning
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
             Train / Validation / Test
                          │
                          ▼
                 Initialize LSTM Model
                          │
                          ▼
                    Model Training
                          │
                          ▼
               Validation Each Epoch
                          │
                          ▼
                Save Best Checkpoint
                          │
                          ▼
                Final Model Evaluation
                          │
                          ▼
                Export Trained Model
```

---

# Training Workflow

1. Load historical market data.
2. Validate the dataset.
3. Remove duplicates and invalid records.
4. Handle missing values.
5. Generate technical indicators.
6. Normalize all input features.
7. Create sequential training samples.
8. Split the dataset.
9. Build the LSTM model.
10. Train using mini-batches.
11. Validate after each epoch.
12. Save the best-performing checkpoint.
13. Evaluate the final model.
14. Export the trained model.

---

# Data Sources

Training data can include:

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

# Feature Engineering

Examples of engineered features include:

* Price Returns
* Log Returns
* Moving Averages
* RSI
* MACD
* ATR
* Bollinger Bands
* VWAP
* Momentum
* Volatility
* Order Book Imbalance
* Funding Rate Change
* Open Interest Change

---

# Dataset Split

A common starting point is:

| Dataset    | Percentage |
| ---------- | ---------: |
| Training   |        70% |
| Validation |        15% |
| Testing    |        15% |

Example

```text
100,000 Samples

↓

70,000 Training

15,000 Validation

15,000 Testing
```

---

# Sequence Generation

The LSTM learns from fixed-length sequences.

Example

```text
Previous 60 Candles

↓

Predict Next Candle
```

Input tensor

```text
(samples, sequence_length, features)
```

Example

```text
(50000, 60, 40)
```

---

# Model Configuration

Example architecture

```text
Input Layer

↓

LSTM (128 Units)

↓

Dropout (0.20)

↓

LSTM (64 Units)

↓

Dropout (0.20)

↓

Dense (32)

↓

Output Layer
```

---

# Hyperparameters

Typical starting values:

| Parameter       | Value |
| --------------- | ----: |
| Sequence Length |    60 |
| Batch Size      |    32 |
| Epochs          |   100 |
| Learning Rate   | 0.001 |
| Hidden Units    |   128 |
| Dropout         |  0.20 |

These values should be tuned based on validation performance.

---

# Loss Functions

## Regression

* Mean Squared Error (MSE)
* Mean Absolute Error (MAE)
* Huber Loss

## Classification

* Cross Entropy Loss

---

# Optimizers

Supported optimizers:

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

# Training Loop

```text
Epoch Start
      │
      ▼
Load Batch
      │
      ▼
Forward Pass
      │
      ▼
Calculate Loss
      │
      ▼
Backpropagation
      │
      ▼
Update Weights
      │
      ▼
Repeat for All Batches
      │
      ▼
Validation
      │
      ▼
Save Best Model
```

---

# Validation

Validation is performed after each epoch to monitor generalization.

Metrics may include:

* Validation Loss
* MAE
* RMSE
* Accuracy
* Precision
* Recall
* F1 Score

Validation results are used to determine whether a checkpoint should be saved.

---

# Early Stopping

Training can stop automatically when validation performance no longer improves.

Benefits:

* Reduces overfitting
* Saves training time
* Preserves the best model

Example

```text
Epoch 41

↓

Validation Loss Stops Improving

↓

Stop Training

↓

Keep Best Checkpoint
```

---

# Checkpointing

Model checkpoints are saved during training.

Directory

```text
checkpoints/

├── best_model.pt
├── latest_model.pt
└── history/
```

The best checkpoint is selected based on validation metrics.

---

# Evaluation

Regression metrics

* MAE
* MSE
* RMSE
* MAPE
* R² Score

Classification metrics

* Accuracy
* Precision
* Recall
* F1 Score

Trading metrics

* Win Rate
* Profit Factor
* Sharpe Ratio
* Maximum Drawdown

---

# Logging

Training logs should record:

* Epoch number
* Training loss
* Validation loss
* Learning rate
* Epoch duration
* Best validation score

Example

```text
Epoch 25/100

Training Loss : 0.0134
Validation Loss : 0.0151
Learning Rate : 0.001
Checkpoint : Saved
```

---

# Model Export

After successful training, export:

```text
checkpoints/

best_model.pt
latest_model.pt
```

Additional artifacts:

```text
outputs/

training_report.csv
loss_curve.png
metrics.json
```

---

# Training Frequency

Suggested retraining schedule:

| Dataset   | Frequency |
| --------- | --------- |
| 1 Minute  | Daily     |
| 5 Minute  | Daily     |
| 15 Minute | Daily     |
| 1 Hour    | Weekly    |
| 4 Hour    | Weekly    |
| 1 Day     | Monthly   |

The schedule should be adjusted if market conditions change significantly or new features are introduced.

---

# Best Practices

* Keep training and inference preprocessing identical.
* Save the fitted scaler and feature configuration.
* Shuffle only where appropriate for sequence generation.
* Monitor validation performance rather than training loss alone.
* Use reproducible random seeds.
* Keep experiments versioned.

---

# Future Improvements

Planned enhancements include:

* Hyperparameter optimization
* Mixed precision training
* Multi-GPU training
* Attention-based LSTM
* Bidirectional LSTM
* Ensemble learning
* Automated retraining
* Experiment tracking

---

# Integration

```text
SQLite Database
        │
        ▼
Preprocessing
        │
        ▼
Feature Engineering
        │
        ▼
Sequence Generation
        │
        ▼
LSTM Training
        │
        ▼
Model Checkpoints
        │
        ▼
Evaluation
        │
        ▼
Inference
```

---

# Summary

The training pipeline converts historical Ethereum market data into a trained LSTM model through preprocessing, feature engineering, sequence generation, optimization, validation, and checkpointing. A disciplined training process, consistent preprocessing, and thorough evaluation provide the foundation for reliable predictions and future extensions such as transformer models, ensemble methods, and reinforcement learning.
