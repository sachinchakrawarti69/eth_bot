"""
Base Dataset Schema

Defines the universal dataset structure shared by all
machine learning datasets in the ETH Bot.

This is the parent schema for:

- Tabular datasets
- Sequence datasets
- Attention datasets
- Transformer datasets
- TFT datasets
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BaseDatasetSchema:
    """
    Common dataset metadata.
    """

    # ==========================================================
    # Asset Information
    # ==========================================================

    symbol: str

    timeframe: str

    # ==========================================================
    # Dataset Identification
    # ==========================================================

    dataset_type: str = "train"
    """
    Dataset split:

    train
    validation
    test
    inference
    """

    dataset_version: str = "1.0"

    # ==========================================================
    # Time Information
    # ==========================================================

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    # ==========================================================
    # Data Quality Metadata
    # ==========================================================

    data_source: Optional[str] = None

    feature_version: Optional[str] = None

    schema_version: str = "1.0"

    # ==========================================================
    # Dataset Status
    # ==========================================================

    is_validated: bool = False

    validation_message: Optional[str] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

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