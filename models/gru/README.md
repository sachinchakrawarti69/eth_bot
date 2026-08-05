# GRU forecasting

This independent package forecasts the next ETH candle from a `(batch, 60, features)` tensor. It provides single, stacked, bidirectional, and attention-GRU regressors. Use `python -m llm.gru.train DATA_DIR --variant attention`; `DATA_DIR` contains the four NumPy training arrays named in `train.py`.

GRUs are efficient recurrent models with update and reset gates. They are cheaper than LSTMs but can have less capacity for very long dependencies. Bidirectional mode is intended for offline research only, not live causal trading.
