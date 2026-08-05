"""Dilated causal residual temporal convolutional network."""
from __future__ import annotations
import tensorflow as tf
from llm.shared import ModelConfig


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class ResidualBlock(tf.keras.layers.Layer):
    """Two causal dilated convolutions with residual and skip connections."""
    def __init__(self, filters: int, dilation_rate: int, dropout: float = 0.0, **kwargs: object) -> None:
        super().__init__(**kwargs); self.filters, self.dilation_rate, self.dropout = filters, dilation_rate, dropout
        self.conv1 = tf.keras.layers.Conv1D(filters, 3, padding="causal", dilation_rate=dilation_rate, activation="relu")
        self.conv2 = tf.keras.layers.Conv1D(filters, 3, padding="causal", dilation_rate=dilation_rate, activation="relu")
        self.drop = tf.keras.layers.Dropout(dropout); self.projection = tf.keras.layers.Conv1D(filters, 1); self.add = tf.keras.layers.Add()
    def call(self, inputs: tf.Tensor, training: bool = False) -> tf.Tensor:
        x = self.drop(self.conv1(inputs), training=training); x = self.drop(self.conv2(x), training=training)
        return tf.nn.relu(self.add([self.projection(inputs), x]))
    def get_config(self) -> dict[str, object]: return {**super().get_config(), "filters": self.filters, "dilation_rate": self.dilation_rate, "dropout": self.dropout}


def build_tcn(config: ModelConfig) -> tf.keras.Model:
    """Build a causal multi-scale TCN for next-candle regression."""
    inputs = tf.keras.Input((config.sequence_length, config.feature_count)); x = inputs
    skips = []
    for rate in (1, 2, 4, 8):
        x = ResidualBlock(config.units, rate, config.dropout, name=f"residual_d{rate}")(x); skips.append(x)
    x = tf.keras.layers.Add(name="skip_aggregation")(skips); x = tf.keras.layers.GlobalAveragePooling1D()(x)
    output = tf.keras.layers.Dense(config.output_units, dtype="float32")(x)
    model = tf.keras.Model(inputs, output, name="tcn"); model.compile(optimizer=tf.keras.optimizers.Adam(config.learning_rate), loss="mse", metrics=["mae"])
    return model
