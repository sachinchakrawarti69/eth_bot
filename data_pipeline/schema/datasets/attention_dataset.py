"""
Attention Dataset Schema

Defines the base structure for attention-based
time-series machine learning datasets in the ETH Bot.

Supported models:

- Transformer
- Temporal Fusion Transformer (TFT)
- Other attention-based architectures

This schema extends SequenceDatasetSchema and provides
common attention-related metadata.
"""

from dataclasses import dataclass
from typing import List, Optional

from .sequence_dataset import SequenceDatasetSchema


@dataclass
class AttentionDatasetSchema(SequenceDatasetSchema):
    """
    Base schema for attention-based sequence models.
    """

    # ==========================================================
    # Attention Configuration
    # ==========================================================

    attention_heads: Optional[int] = None

    # ==========================================================
    # Attention Mask
    #
    # Shape:
    # (sequence_length,)
    #
    # 1 = valid token
    # 0 = padding
    # ==========================================================

    attention_mask: Optional[List[int]] = None

    # ==========================================================
    # Padding Mask
    #
    # Used for variable length sequences
    # ==========================================================

    padding_mask: Optional[List[int]] = None

    # ==========================================================
    # Positional Information
    # ==========================================================

    position_ids: Optional[List[int]] = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def attention_shape(self):
        if self.features:
            return (
                len(self.features),
                len(self.features[0]),
            )

        return None

    @property
    def has_attention_mask(self):
        return self.attention_mask is not None

    @property
    def has_padding(self):
        return self.padding_mask is not None