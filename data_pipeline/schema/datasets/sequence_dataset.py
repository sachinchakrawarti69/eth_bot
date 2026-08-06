"""
Sequence Dataset Schema

Defines the base structure for all sequence-based
machine learning datasets in the ETH Bot.

Supported models:

- LSTM
- GRU
- Transformer
- Temporal Fusion Transformer (TFT)

This schema extends BaseDatasetSchema and provides
common time-series sequence metadata.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .base_dataset import BaseDatasetSchema


@dataclass
class SequenceDatasetSchema(BaseDatasetSchema):
    """
    Base schema for sequence-based ML models.
    """

    # ==========================================================
    # Sequence Configuration
    # ==========================================================

    sequence_length: int = 0

    prediction_horizon: int = 1

    feature_count: int = 0

    # ==========================================================
    # Sequence Time Information
    # ==========================================================

    sequence_start: Optional[datetime] = None

    sequence_end: Optional[datetime] = None

    prediction_timestamp: Optional[datetime] = None

    # ==========================================================
    # Sequence Features
    #
    # Shape:
    # (sequence_length, feature_count)
    # ==========================================================

    features: Optional[List[List[float]]] = None

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
    # Convenience Properties
    # ==========================================================

    @property
    def input_shape(self):
        return (
            self.sequence_length,
            self.feature_count,
        )

    @property
    def sequence_size(self):
        return self.sequence_length * self.feature_count