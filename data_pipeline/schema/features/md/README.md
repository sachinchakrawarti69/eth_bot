# Feature Schemas

## Overview

The **Feature Schemas** define the standardized structure for all engineered machine learning features used throughout the ETH Bot.

Feature engineering transforms cleaned and processed datasets into **AI-ready numerical features** that capture market behavior, price action, liquidity, derivatives positioning, blockchain activity, sentiment, and temporal patterns.

Unlike raw or processed datasets, feature schemas contain only engineered variables designed for predictive modeling.

---

# Directory Structure

```text
features/
│
├── README.md
│
├── price_features.py
├── price_features.md
│
├── volume_features.py
├── volume_features.md
│
├── derivative_features.py
├── derivative_features.md
│
├── orderbook_features.py
├── orderbook_features.md
│
├── sentiment_features.py
├── sentiment_features.md
│
├── onchain_features.py
├── onchain_features.md
│
├── time_features.py
├── time_features.md
```

---

# Pipeline Position

```mermaid
flowchart LR

Raw Data

-->

Processed Data

-->

Feature Engineering

-->

Feature Schemas

-->

Merged Dataset

-->

AI Models
```

---

# Feature Categories

```mermaid
mindmap

root((Feature Schemas))

    Price Features

    Volume Features

    Derivative Features

    Order Book Features

    Sentiment Features

    On-Chain Features

    Time Features
```

---

# Feature Overview

| Schema | Purpose |
|----------|----------|
| **Price Features** | Engineered price action, returns, trend strength, momentum, volatility, and statistical price features |
| **Volume Features** | Trading activity, liquidity, buying/selling pressure, VWAP, and volume profile features |
| **Derivative Features** | Futures and options positioning, leverage, funding, liquidations, Greeks, and market stress |
| **Order Book Features** | Market microstructure, liquidity, spreads, depth, order flow, slippage, and price pressure |
| **Sentiment Features** | News, Fear & Greed, social media, NLP, and LLM-derived market sentiment |
| **On-Chain Features** | Ethereum network activity, exchange flows, whale activity, staking, and smart money behavior |
| **Time Features** | Trading sessions, cyclical encoding, calendar effects, seasonality, and temporal patterns |

---

# Feature Engineering Workflow

```mermaid
flowchart TD

Processed Market Data

-->

Price Features

Processed Volume Data

-->

Volume Features

Processed Derivatives

-->

Derivative Features

Processed Order Book

-->

Order Book Features

Processed Sentiment

-->

Sentiment Features

Processed On-Chain Data

-->

On-Chain Features

Timestamp

-->

Time Features

Price Features

-->

Merged Feature Dataset

Volume Features

-->

Merged Feature Dataset

Derivative Features

-->

Merged Feature Dataset

Order Book Features

-->

Merged Feature Dataset

Sentiment Features

-->

Merged Feature Dataset

On-Chain Features

-->

Merged Feature Dataset

Time Features

-->

Merged Feature Dataset
```

---

# Relationship with Other Schemas

```mermaid
flowchart TD

Raw Schemas

-->

Processed Schemas

Processed Schemas

-->

Feature Schemas

Feature Schemas

-->

Merged Dataset

Merged Dataset

-->

AI Models

AI Models

-->

Strategy Engine

Strategy Engine

-->

Risk Engine

Risk Engine

-->

Execution Engine
```

---

# Downstream Usage

```mermaid
mindmap

root((Feature Schemas))

    AI Models

    Dataset Builder

    Strategy Engine

    Risk Engine

    Paper Trading

    Backtesting

    Live Trading

    Monitoring
```

---

# Design Principles

```mermaid
mindmap

root((Feature Design))

    Deterministic

    AI Ready

    Time-Series Native

    Exchange Independent

    Modular

    Lightweight

    Extensible

    Reproducible
```

---

# Data Flow

```mermaid
flowchart LR

Collectors

-->

Raw Storage

-->

Raw Schemas

-->

Processing Pipeline

-->

Processed Schemas

-->

Feature Engineering

-->

Feature Schemas

-->

Merged Dataset

-->

Model Training

-->

Model Registry

-->

Inference

-->

Strategy Engine

-->

Risk Engine

-->

Execution Engine
```

---

# Machine Learning Integration

```mermaid
flowchart TD

Feature Schemas

-->

Feature Store

-->

Training Dataset

-->

Feature Selection

-->

Model Training

-->

Model Validation

-->

Model Registry

-->

Inference Pipeline
```

Supported model families include:

- LSTM
- GRU
- Temporal Convolutional Networks (TCN)
- Transformers
- XGBoost
- LightGBM
- CatBoost
- Random Forest
- Ensemble Models

---

# Future Feature Schemas

As the project evolves, additional feature schemas may be introduced:

```text
features/
│
├── statistical_features.py
├── regime_features.py
├── volatility_surface_features.py
├── options_features.py
├── cross_asset_features.py
├── execution_features.py
├── macro_features.py
├── reinforcement_features.py
└── graph_features.py
```

These should be added only when corresponding data sources and use cases are available.

---

# Summary

The **Feature Schemas** form the machine learning layer of the ETH Bot data pipeline. They transform processed market, derivatives, order book, sentiment, on-chain, and temporal data into standardized, AI-ready numerical representations.

By separating engineered features from raw and processed datasets, the pipeline remains modular, reproducible, and scalable, enabling efficient feature selection, model training, backtesting, paper trading, live trading, and continuous model improvement across the entire ETH futures trading system.

```mermaid
flowchart TD

Raw Data

-->

Processed Data

-->

Feature Engineering

-->

Feature Schemas

-->

Merged Feature Dataset

-->

AI Models

-->

Strategy Engine

-->

Risk Engine

-->

Execution Engine

-->

Monitoring

Monitoring

-->

Model Retraining
```