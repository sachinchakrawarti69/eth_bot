# Raw OHLCV Schema

## Overview

The **Raw OHLCV Schema** defines the standard structure for candlestick (Kline) data collected from cryptocurrency exchanges.

Every exchange has its own response format. Before entering the data pipeline, all OHLCV data is transformed into this common schema.

This ensures every downstream component works with a single standardized format.

---

# Pipeline Position

```mermaid
flowchart TD

A[Exchange API]

--> B[Collector]

--> C[Raw OHLCV Schema]

--> D[Validation]

--> E[Processing]

--> F[Technical Indicators]

--> G[Feature Engineering]

--> H[Dataset Builder]

--> I[AI Models]
```

---

# Purpose

The schema provides a universal structure for market candles.

Supported exchanges include:

- Binance
- Bybit
- OKX

Future exchanges can be integrated without changing downstream components.

---

# Supported Markets

```mermaid
flowchart LR

A[Market]

--> B[Spot]

A --> C[USDT Futures]

A --> D[Coin-M Futures]

A --> E[Options Future]
```

---

# Supported Timeframes

```mermaid
mindmap
root((Timeframes))
    Seconds
        1s
        5s
        15s
    Minutes
        1m
        3m
        5m
        15m
        30m
    Hours
        1h
        2h
        4h
        6h
        8h
        12h
    Days
        1d
        3d
    Weeks
        1w
    Months
        1M
```

The schema is identical for every timeframe.

Only the candle duration changes.

---

# OHLCV Structure

```mermaid
classDiagram

class OHLCV{

exchange

symbol

market

timeframe

open_time

close_time

open

high

low

close

volume

quote_volume

number_of_trades

taker_buy_base_volume

taker_buy_quote_volume

}
```

---

# Field Definitions

| Field | Type | Description |
|---------|------|-------------|
| exchange | string | Exchange name |
| symbol | string | Trading symbol |
| market | string | Spot / Futures |
| timeframe | string | Candle interval |
| open_time | datetime | Candle start |
| close_time | datetime | Candle end |
| open | float | Opening price |
| high | float | Highest price |
| low | float | Lowest price |
| close | float | Closing price |
| volume | float | Base asset volume |
| quote_volume | float | Quote asset volume |
| number_of_trades | integer | Number of trades |
| taker_buy_base_volume | float | Buy volume |
| taker_buy_quote_volume | float | Buy quote volume |

---

# Example Record

```json
{
  "exchange": "binance",
  "symbol": "ETHUSDT",
  "market": "futures",
  "timeframe": "1h",

  "open_time": "2026-08-01T10:00:00Z",
  "close_time": "2026-08-01T10:59:59Z",

  "open": 3510.25,
  "high": 3528.40,
  "low": 3498.15,
  "close": 3521.90,

  "volume": 12453.20,
  "quote_volume": 43874210.15,

  "number_of_trades": 14520,

  "taker_buy_base_volume": 6325.42,
  "taker_buy_quote_volume": 22340015.92
}
```

---

# Validation Rules

```mermaid
flowchart TD

A[Incoming Candle]

--> B{Required Fields?}

B -- No --> X[Reject]

B -- Yes --> C{Valid Prices?}

C -- No --> X

C -- Yes --> D{Valid Volume?}

D -- No --> X

D -- Yes --> E{Valid Timestamp?}

E -- No --> X

E -- Yes --> F[Accept]
```

---

# Price Rules

```mermaid
flowchart LR

A[High]

--> B[>= Open]

A --> C[>= Close]

D[Low]

--> E[<= Open]

D --> F[<= Close]

A --> G[>= Low]
```

---

# Data Processing Lifecycle

```mermaid
flowchart TD

A[Raw Exchange Response]

-->

B[Schema Validation]

-->

C[Data Cleaning]

-->

D[Time Alignment]

-->

E[Processed Market Data]

-->

F[Technical Indicators]

-->

G[Feature Engineering]

-->

H[Training Dataset]
```

---

# Data Sources

```mermaid
flowchart LR

A[Binance]

--> E[Collector]

B[Bybit]

--> E

C[OKX]

--> E

D[CSV]

--> E

E

--> F[Raw OHLCV Schema]
```

---

# Relationship With Other Schemas

```mermaid
flowchart TD

A[Raw OHLCV]

-->

B[Processed Schema]

-->

C[Indicator Schema]

-->

D[Feature Schema]

-->

E[Dataset Schema]

-->

F[AI Models]
```

---

# Design Principles

```mermaid
mindmap
root((Schema))
    Exchange Independent
    Timeframe Independent
    Strong Validation
    Easy Serialization
    Extensible
    Reusable
    Versionable
```

---

# Future Extensions

```mermaid
flowchart LR

A[Current Schema]

-->

B[VWAP]

-->

C[Typical Price]

-->

D[Median Price]

-->

E[Weighted Close]

-->

F[Quality Score]

-->

G[Latency Metrics]
```

---

# Complete Data Flow

```mermaid
flowchart TD

Exchange

--> Collector

--> Raw OHLCV Schema

--> Validation

--> Processing

--> Technical Indicators

--> Feature Engineering

--> Dataset Builder

--> AI Models

--> Strategy Engine

--> Risk Engine

--> Execution Engine
```

---

# Summary

The Raw OHLCV Schema is the canonical representation of candlestick market data within the project.

Every exchange-specific response is transformed into this standardized schema before moving through validation, processing, feature engineering, dataset creation, and AI model training. It provides a consistent, reliable foundation for the entire trading system.