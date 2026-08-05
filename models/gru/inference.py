"""GRU real-time inference API."""
import numpy as np
import tensorflow as tf
class GRUInference:
    """Loads one GRU model and predicts a next candle from one window."""
    def __init__(self, model_path: str) -> None: self.model = tf.keras.models.load_model(model_path)
    def next_candle(self, window: np.ndarray) -> float: return float(self.model.predict(np.asarray(window, dtype=np.float32)[None, ...], verbose=0).ravel()[0])
