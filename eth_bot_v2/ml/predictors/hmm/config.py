"""Hyperparameters for the HMM predictor."""

MODEL_NAME = "hmm"

HYPERPARAMS = {
    "n_components": 3,
    "covariance_type": "diag",
    "n_iter": 100,
    "random_state": 42,
}

FEATURES = ["close"]         # HMM uses returns only
TARGET   = "dir_24h"         # not used during fit, only for evaluation
