"""Re-export so `ml.predictors.<name>.train(...)` works."""

from .train   import train
from .predict import predict
from .explain import explain

__all__ = ["train", "predict", "explain"]
