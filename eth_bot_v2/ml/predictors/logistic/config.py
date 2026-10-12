"""Hyperparameters for the logistic predictor."""

MODEL_NAME = "logistic"

HYPERPARAMS = {
    "C": 1.0,
    "max_iter": 1000,
    "class_weight": None,
    "solver": "lbfgs",
    "random_state": 42,
}

FEATURES = [
    "rsi_14", "macd_hist", "vol_20",
    "dist_sma50", "dist_sma200",
    "funding", "hour",
]

TARGET = "dir_24h"
