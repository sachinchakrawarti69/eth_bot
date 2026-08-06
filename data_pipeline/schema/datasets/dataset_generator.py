"""
Dataset Generator

Builds model-specific datasets from the merged feature dataset.

Responsibilities
----------------
- Generate tabular datasets
- Generate sequence datasets
- Generate attention datasets
- Split train/validation/test
- Prepare inference datasets
"""

from typing import Any

from .xgboost import XGBoostDatasetSchema
from .lightgbm import LightGBMDatasetSchema
from .lstm import LSTMDatasetSchema
from .transformer import TransformerDatasetSchema
from .tft import TFTDatasetSchema


class DatasetGenerator:
    """
    Factory responsible for creating datasets
    for different ML models.
    """

    def __init__(self, config: dict):
        self.config = config

    # ---------------------------------------------------------
    # Tabular Models
    # ---------------------------------------------------------

    def build_xgboost_dataset(self, data: Any):
        """Generate XGBoost dataset."""
        raise NotImplementedError

    def build_lightgbm_dataset(self, data: Any):
        """Generate LightGBM dataset."""
        raise NotImplementedError

    # ---------------------------------------------------------
    # Sequence Models
    # ---------------------------------------------------------

    def build_lstm_dataset(self, data: Any):
        """Generate LSTM dataset."""
        raise NotImplementedError

    # ---------------------------------------------------------
    # Attention Models
    # ---------------------------------------------------------

    def build_transformer_dataset(self, data: Any):
        """Generate Transformer dataset."""
        raise NotImplementedError

    def build_tft_dataset(self, data: Any):
        """Generate TFT dataset."""
        raise NotImplementedError

    # ---------------------------------------------------------
    # Dataset Split
    # ---------------------------------------------------------

    def train_validation_test_split(self, dataset: Any):
        """Split dataset into train, validation, and test."""
        raise NotImplementedError

    # ---------------------------------------------------------
    # Live Inference
    # ---------------------------------------------------------

    def build_live_dataset(self, latest_data: Any):
        """Create dataset for live prediction."""
        raise NotImplementedError