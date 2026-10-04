# Ethereum Bot Commands

Project Path

```text
D:\Sachin Chakrawarti\Learn\Done\myprojets\projects\project_peace\ethereum\eth_bot
```

---

# Virtual Environment

## Create Virtual Environment (Python 3.10)

```cmd
py -3.10 -m venv .venv
```

## Activate

```cmd
.venv\Scripts\activate
```

## Verify Python Version

```cmd
python --version
```

Expected:

```text
Python 3.10.x
```

## Upgrade Pip

```cmd
python -m pip install --upgrade pip
```

## Install Dependencies

```cmd
pip install -r requirements.txt
```

## Save Installed Packages

```cmd
pip freeze > requirements.txt
```

## Deactivate

```cmd
deactivate
```

---

# Database Schemas

## OHLCV

```cmd
sqlite3 storage\database\ETH.db < schema\0001_ohlcv.sql
```

## Orderbook

```cmd
sqlite3 storage\database\ETH.db < schema\0002_orderbook.sql
```

## Open Interest

```cmd
sqlite3 storage\database\ETH.db < schema\0004_open_interest.sql
```

## Funding Rate

```cmd
sqlite3 storage\database\ETH.db < schema\0005_funding_rate.sql
```

## Trades

```cmd
sqlite3 storage\database\ETH.db < schema\0006_trades.sql
```

## Option Chain

```cmd
sqlite3 storage\database\ETH.db < schema\0007_option_chain.sql
```

## Greeks

```cmd
sqlite3 storage\database\ETH.db < schema\0008_greeks.sql
```

## Implied Volatility

```cmd
sqlite3 storage\database\ETH.db < schema\0009_implied_volatility.sql
```

## Liquidations

```cmd
sqlite3 storage\database\ETH.db < schema\0010_liquidations.sql
```

## News

```cmd
sqlite3 storage\database\ETH.db < schema\0011_news.sql
```

## On-chain

```cmd
sqlite3 storage\database\ETH.db < schema\0012_onchain.sql
```

## Whales

```cmd
sqlite3 storage\database\ETH.db < schema\0013_whales.sql
```

## Fear & Greed

```cmd
sqlite3 storage\database\ETH.db < schema\0014_fear_greed.sql
```

---

# Data Collection

## OHLCV

```cmd
python -m scripts.ohlcv.collect_ohlcv
```

## Orderbook

```cmd
python -m scripts.orderbook.collect_orderbook
```

## Open Interest

```cmd
python -m scripts.open_interest.collect_open_interest
```

## Funding Rate

```cmd
python -m scripts.funding_rate.collect_funding_rate
```

## Trades

```cmd
python -m scripts.trades.collect_trades
```

## Option Chain

```cmd
python -m scripts.option_chain.collect_option_chain
```

## Greeks

```cmd
python -m scripts.greeks.collect_greeks
```

## Implied Volatility

```cmd
python -m scripts.implied_volatility.collect_implied_volatility
```

## Liquidations

```cmd
python -m scripts.liquidations.collect_liquidations
```

## News

```cmd
python -m scripts.news.collect_news
```

## On-chain

```cmd
python -m scripts.onchain.collect_onchain
```

## Whales

```cmd
python -m scripts.whales.collect_whales
```

## Fear & Greed

```cmd
python -m scripts.fear_greed.collect_fear_greed
```

---

# LSTM Unit Tests

## Load Data

```cmd
python -m llm.lstm.unittests.test_load_data
```

## Clean Data

```cmd
python -m llm.lstm.unittests.test_clean_data
```

## Merge Data

```cmd
python -m llm.lstm.unittests.test_merge_data
```

## Technical Indicators

```cmd
python -m llm.lstm.unittests.test_technical_indicators
```

## Feature Engineering

```cmd
python -m llm.lstm.unittests.test_feature_engineering
```

## Normalize

```cmd
python -m llm.lstm.unittests.test_normalize
```

## Create Sequences

```cmd
python -m llm.lstm.unittests.test_create_sequences
```

## Create Labels

```cmd
python -m llm.lstm.unittests.test_create_labels
```

## Split Dataset

```cmd
python -m llm.lstm.unittests.test_split_dataset
```

## Pipeline

```cmd
python -m llm.lstm.unittests.test_pipeline
```

## Dataset

```cmd
python -m llm.lstm.unittests.test_dataset
```

## DataLoader

```cmd
python -m llm.lstm.unittests.test_dataloader
```

## Sequence Dataset

```cmd
python -m llm.lstm.unittests.test_sequence_dataset
```

---

# Model Tests

## LSTM Model

```cmd
python -m llm.lstm.unittests.models.test_lstm_model
```

## Stacked LSTM

```cmd
python -m llm.lstm.unittests.models.test_stacked_lstm
```

## Bidirectional LSTM

```cmd
python -m llm.lstm.unittests.models.test_bidirectional_lstm
```

## Attention LSTM

```cmd
python -m llm.lstm.unittests.models.test_attention_lstm
```

## Encoder

```cmd
python -m llm.lstm.unittests.models.test_encoder
```

## Decoder

```cmd
python -m llm.lstm.unittests.models.test_decoder
```

## Layers

```cmd
python -m llm.lstm.unittests.models.test_layers
```

---

# Training

## Trainer

```cmd
python -m llm.lstm.unittests.training.test_trainer
```

---

# Useful Commands

## Check Installed Python Versions

```cmd
py --list
```

## Check Current Python

```cmd
python --version
```

## Check Pip

```cmd
python -m pip --version
```

## Install TensorFlow

```cmd
pip install tensorflow
```

## Install All Requirements

```cmd
pip install -r requirements.txt
```

## List Installed Packages

```cmd
pip list
```

## Freeze Environment

```cmd
pip freeze > requirements.txt
```

python database\show.py
python database\show.py funding_rate
python database\show.py fear_greed
python -m scripts_python.update_market
