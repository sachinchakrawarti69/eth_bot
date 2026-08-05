# Temporal Fusion Transformer

TFT forecasts quantiles (10th, 50th, 90th percentile by default) for next ETH candles from dynamic covariates. It combines feature selection, gated residual networks, an LSTM temporal encoder, and temporal multi-head attention. Run `python -m llm.temporal_fusion_transformer.train DATA_DIR`.

Quantile ranges express uncertainty useful for risk controls. TFT is more interpretable than a plain Transformer but costs more compute and needs carefully aligned covariates.
