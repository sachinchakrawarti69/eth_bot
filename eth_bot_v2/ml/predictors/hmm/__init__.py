"""Re-export so `ml.predictors.hmm.train(...)` works."""

from .train   import train
from .predict import predict, current_state
from .explain import explain

__all__ = ["train", "predict", "current_state", "explain"]
