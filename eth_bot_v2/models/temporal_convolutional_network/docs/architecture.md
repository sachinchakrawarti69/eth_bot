# Architecture

Four residual blocks use dilation rates 1, 2, 4, and 8. Causal padding ensures each output only sees earlier candles. Aggregated skip paths retain multi-scale signals before the regression head.
