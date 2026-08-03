# Architecture

Each variant maps historical feature vectors to a scalar next-candle forecast. Attention GRU computes a normalized weight for each hidden state before the output layer, making influential candles inspectable.
