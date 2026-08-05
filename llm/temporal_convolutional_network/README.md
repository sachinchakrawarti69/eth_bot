# Temporal Convolutional Network

This package produces next-candle forecasts from `(batch, time, features)` windows using dilated causal convolutions, residual blocks, skip aggregation, and multi-scale temporal features. Run `python -m llm.temporal_convolutional_network.train DATA_DIR`.

Causal convolutions prevent future leakage and train in parallel. Their receptive field must be configured large enough for the trading horizon; very long contexts can require many dilation levels.
