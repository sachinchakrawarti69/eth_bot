# Model

The output predicts quantiles with pinball loss: `max(q(y−ŷ), (q−1)(y−ŷ))`. Set `static_feature_count` to expose a separate static-covariates input; it is projected and repeated as contextual state before temporal modeling.
