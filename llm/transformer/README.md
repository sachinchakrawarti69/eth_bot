# Time-Series Transformer

The Transformer consumes scaled candle windows `(batch, time, features)` and returns a next-candle regression value. It uses sinusoidal positional encoding, multi-head self-attention, feed-forward layers, and residual normalization. Run `python -m llm.transformer.train DATA_DIR`.

Attention models long-range relationships and parallelize well, but require more data and memory than GRUs. The encoder supplies temporal context; the output head acts as the forecasting decoder.
