"""
Temporal Fusion Transformer (TFT) Dataset Schema

Defines the dataset structure used for training and inference
with Temporal Fusion Transformer (TFT) models.

The dataset is generated from the merged feature dataset after
feature engineering and sequence generation.

This schema stores static features, historical sequences,
known future features, and prediction targets.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class TFTDatasetSchema:

    # ==========================================================
    # Dataset Metadata
    # ==========================================================

    symbol: str
    timeframe: str

    encoder_length: int
    decoder_length: int

    feature_count: int

    # ==========================================================
    # Sequence Information
    # ==========================================================

    encoder_start: datetime
    encoder_end: datetime

    decoder_start: datetime
    decoder_end: datetime

    prediction_timestamp: datetime

    # ==========================================================
    # Static Features
    # ==========================================================

    static_features: List[float]

    # ==========================================================
    # Historical Encoder Features
    # Shape:
    # (encoder_length, feature_count)
    # ==========================================================

    encoder_features: List[List[float]]

    # ==========================================================
    # Future Known Decoder Features
    # Shape:
    # (decoder_length, feature_count)
    # ==========================================================

    decoder_features: List[List[float]]

    # ==========================================================
    # Attention Mask (Optional)
    # ==========================================================

    attention_mask: Optional[List[int]] = None

    # ==========================================================
    # Target Labels
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

    # ==========================================================
    # Metadata
    # ==========================================================

    dataset_version: str = "1.0"

    generated_at: Optional[datetime] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def encoder_shape(self):
        return (
            self.encoder_length,
            self.feature_count,
        )

    @property
    def decoder_shape(self):
        return (
            self.decoder_length,
            self.feature_count,
        )

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