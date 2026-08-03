"""Graph construction for asset relationship modelling."""
from __future__ import annotations
import numpy as np

def correlation_adjacency(asset_returns: np.ndarray, threshold: float = 0.0) -> np.ndarray:
    """Create a symmetric edge matrix from asset-return correlations."""
    returns = np.asarray(asset_returns, dtype=np.float32)
    if returns.ndim != 2 or returns.shape[1] < 1: raise ValueError("asset_returns must be (observations, assets)")
    matrix = np.corrcoef(returns, rowvar=False); matrix = np.nan_to_num(matrix)
    return (np.abs(matrix) >= threshold).astype(np.float32)
