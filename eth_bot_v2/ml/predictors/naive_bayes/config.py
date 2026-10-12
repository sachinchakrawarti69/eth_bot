"""Hyperparameters for the Gaussian Naive Bayes predictor."""

MODEL_NAME = "naive_bayes"

HYPERPARAMS = {
    "var_smoothing": 1e-9,
}

FEATURES = [
    "rsi_14", "macd_hist", "vol_20",
    "dist_sma50", "funding", "hour",
]

TARGET = "dir_24h"
