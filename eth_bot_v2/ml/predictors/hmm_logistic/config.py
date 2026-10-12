"""Hyperparameters for the HMM + state-conditional logistic predictor."""

MODEL_NAME = "hmm_logistic"

HMM_PARAMS = {
    "n_components": 3,
    "covariance_type": "diag",
    "n_iter": 100,
    "random_state": 42,
}

LOGISTIC_PARAMS = {
    "C": 1.0,
    "max_iter": 1000,
    "random_state": 42,
}

FEATURES = [
    "rsi_14", "macd_hist", "vol_20",
    "dist_sma50", "dist_sma200",
    "funding", "hour",
]

TARGET = "dir_24h"
