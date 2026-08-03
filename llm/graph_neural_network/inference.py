"""Real-time GNN inference service."""
import numpy as np, tensorflow as tf
class GNNInference:
    def __init__(self, model_path: str) -> None: self.model=tf.keras.models.load_model(model_path)
    def predict_assets(self, nodes: np.ndarray, edges: np.ndarray) -> np.ndarray: return self.model.predict([nodes, edges], verbose=0)
