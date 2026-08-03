# Dataset

Dynamic covariates have shape `(batch, time, features)`. Keep static features constant within a window and append/broadcast them deliberately; never fit preprocessing over validation or test periods.
