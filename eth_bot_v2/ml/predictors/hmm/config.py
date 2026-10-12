"""Hyperparameters for the HMM predictor."""

MODEL_NAME = "hmm"

HYPERPARAMS = {
    "n_components": 3,
    "covariance_type": "diag",
    "n_iter": 100,
    "random_state": 42,
}

FEATURES = ["close"]
TARGET = "dir_24h"
