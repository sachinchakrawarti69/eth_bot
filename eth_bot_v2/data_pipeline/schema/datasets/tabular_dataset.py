"""
Base Tabular Dataset Schema

Defines the common dataset structure used by
tabular machine learning models.

Supported models include:

- XGBoost
- LightGBM
- CatBoost
- Random Forest
- Extra Trees
- Logistic Regression
- Linear Regression
- SVM
- KNN
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class TabularDatasetSchema:
    """
    Base dataset for tabular ML models.
    """

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
    # Feature Vector
    # Shape:
    # (feature_count,)
    # ==========================================================

    features: List[float]

    # ==========================================================
    # Labels
    # ==========================================================

    target_price: Optional[float] = None

    target_return: Optional[float] = None

    target_direction: Optional[int] = None

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