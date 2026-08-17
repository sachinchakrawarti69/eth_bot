"""
LightGBM Dataset Schema

Defines the dataset structure used for training and inference
with LightGBM models.

The dataset is generated from the merged feature dataset after
feature engineering.

This schema stores feature vectors and prediction targets only.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class LightGBMDatasetSchema:

    # ==========================================================
    # Dataset Metadata
    # ==========================================================

    symbol: str
    timeframe: str

    feature_count: int

    prediction_horizon: int

    # ==========================================================
    # Sample Information
    # ==========================================================

    timestamp: datetime

    prediction_timestamp: datetime

    # ==========================================================
    # Input Features
    # Shape:
    # (feature_count,)
    # ==========================================================

    features: List[float]

    # ==========================================================
    # Target Labels
    # ==========================================================

    target_price: Optional[float] = None

    target_return: Optional[float] = None

    target_direction: Optional[int] = None
    # 1 = Bullish
    # 0 = Neutral
    # -1 = Bearish

    target_volatility: Optional[float] = None

    target_regime: Optional[int] = None

    # ==========================================================
    # Sample Weight
    # ==========================================================

    sample_weight: float = 1.0

    # ==========================================================
    # Dataset Split
    # ==========================================================

    dataset_type: str = "train"
    # train
    # validation
    # test
    # inference

    # ==========================================================
    # Metadata
    # ==========================================================

    dataset_version: str = "1.0"

    generated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def input_shape(self):
        return (self.feature_count,)

    @property
    def is_training(self):
        return self.dataset_type == "train"

    @property
    def is_validation(self):
        return self.dataset_type == "validation"

    @property
    def is_testing(self):
        return self.dataset_type == "test"

    @property
    def is_inference(self):
        return self.dataset_type == "inference"