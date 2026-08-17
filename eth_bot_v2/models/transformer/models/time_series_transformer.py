"""Encoder-decoder Transformer components for time-series prediction."""
from __future__ import annotations
import tensorflow as tf
from models.shared import ModelConfig


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class PositionalEncoding(tf.keras.layers.Layer):
    """Adds sinusoidal positions so attention can distinguish candle order."""
    def call(self, inputs: tf.Tensor) -> tf.Tensor:
        length, dimension = tf.shape(inputs)[1], tf.shape(inputs)[2]
        positions = tf.cast(tf.range(length)[:, None], tf.float32)
        indices = tf.cast(tf.range(dimension)[None, :], tf.float32)
        rates = 1.0 / tf.pow(10000.0, (2.0 * tf.floor(indices / 2.0)) / tf.cast(dimension, tf.float32))
        angles = positions * rates
        encoding = tf.where(tf.cast(tf.math.floormod(indices, 2), tf.bool), tf.cos(angles), tf.sin(angles))
        return inputs + encoding[None, :, :]


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class TransformerBlock(tf.keras.layers.Layer):
    """Pre-norm multi-head self-attention plus position-wise feed-forward layer."""
    def __init__(self, units: int, heads: int, dropout: float = 0.0, **kwargs: object) -> None:
        super().__init__(**kwargs); self.units, self.heads, self.dropout = units, heads, dropout
        self.attention = tf.keras.layers.MultiHeadAttention(num_heads=heads, key_dim=units // heads)
        self.ffn = tf.keras.Sequential([tf.keras.layers.Dense(units * 2, activation="gelu"), tf.keras.layers.Dense(units)])
        self.norm1, self.norm2 = tf.keras.layers.LayerNormalization(), tf.keras.layers.LayerNormalization()
        self.drop1, self.drop2 = tf.keras.layers.Dropout(dropout), tf.keras.layers.Dropout(dropout)
    def call(self, inputs: tf.Tensor, training: bool = False) -> tf.Tensor:
        x = self.norm1(inputs); x = inputs + self.drop1(self.attention(x, x, training=training), training=training)
        return x + self.drop2(self.ffn(self.norm2(x), training=training), training=training)
    def get_config(self) -> dict[str, object]: return {**super().get_config(), "units": self.units, "heads": self.heads, "dropout": self.dropout}


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class TransformerEncoder(TransformerBlock):
    """Named encoder layer exposing self-attention over historical candles."""


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class TransformerDecoder(tf.keras.layers.Layer):
    """Cross-attention decoder that reads encoded history from a forecast query."""
    def __init__(self, units: int, heads: int, **kwargs: object) -> None:
        super().__init__(**kwargs); self.units, self.heads = units, heads
        self.cross_attention = tf.keras.layers.MultiHeadAttention(num_heads=heads, key_dim=units // heads)
        self.norm = tf.keras.layers.LayerNormalization()
    def call(self, inputs: tuple[tf.Tensor, tf.Tensor]) -> tf.Tensor:
        query, encoded = inputs
        return self.norm(query + self.cross_attention(query, encoded))
    def get_config(self) -> dict[str, object]: return {**super().get_config(), "units": self.units, "heads": self.heads}


def build_transformer(config: ModelConfig) -> tf.keras.Model:
    """Build a complete causal-style encoder Transformer forecasting next close."""
    if config.units % config.num_heads:
        raise ValueError("units must be divisible by num_heads")
    inputs = tf.keras.Input((config.sequence_length, config.feature_count))
    x = tf.keras.layers.Dense(config.units)(inputs); x = PositionalEncoding()(x)
    x = TransformerEncoder(config.units, config.num_heads, config.dropout)(x)
    x = TransformerEncoder(config.units, config.num_heads, config.dropout)(x)
    query = tf.keras.layers.Lambda(lambda sequence: sequence[:, -1:, :], name="forecast_query")(x)
    x = TransformerDecoder(config.units, config.num_heads)([query, x])
    x = tf.keras.layers.Flatten()(x); x = tf.keras.layers.Dropout(config.dropout)(x)
    output = tf.keras.layers.Dense(config.output_units, dtype="float32")(x)
    model = tf.keras.Model(inputs, output, name="time_series_transformer")
    model.compile(optimizer=tf.keras.optimizers.Adam(config.learning_rate), loss="mse", metrics=["mae"])
    return model
