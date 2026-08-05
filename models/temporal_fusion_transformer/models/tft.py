"""Compact Temporal Fusion Transformer with interpretable variable selection."""
from __future__ import annotations
import tensorflow as tf
from models.shared import ModelConfig


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class GatedResidualNetwork(tf.keras.layers.Layer):
    """Nonlinear transform with an adaptive gate and residual shortcut."""
    def __init__(self, units: int, dropout: float = 0.0, **kwargs: object) -> None:
        super().__init__(**kwargs); self.units, self.dropout = units, dropout
        self.dense1 = tf.keras.layers.Dense(units, activation="elu"); self.dense2 = tf.keras.layers.Dense(units)
        self.gate = tf.keras.layers.Dense(units, activation="sigmoid"); self.skip = tf.keras.layers.Dense(units); self.norm = tf.keras.layers.LayerNormalization()
    def call(self, x: tf.Tensor, training: bool = False) -> tf.Tensor: return self.norm(self.skip(x) + self.gate(x) * self.dense2(self.dense1(x)))
    def get_config(self) -> dict[str, object]: return {**super().get_config(), "units": self.units, "dropout": self.dropout}


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class VariableSelectionNetwork(tf.keras.layers.Layer):
    """Produces a weighted representation of temporal input variables."""
    def __init__(self, units: int, feature_count: int, **kwargs: object) -> None:
        super().__init__(**kwargs); self.units, self.feature_count = units, feature_count
        self.weights_layer = tf.keras.layers.Dense(feature_count, activation="softmax")
        self.transforms = [GatedResidualNetwork(units) for _ in range(feature_count)]
    def call(self, x: tf.Tensor, training: bool = False) -> tf.Tensor:
        weights = self.weights_layer(x)
        transformed = tf.stack([layer(x[..., index:index + 1], training=training) for index, layer in enumerate(self.transforms)], axis=-2)
        return tf.reduce_sum(transformed * weights[..., None], axis=-2)
    def get_config(self) -> dict[str, object]: return {**super().get_config(), "units": self.units, "feature_count": self.feature_count}


def quantile_loss(quantiles: tuple[float, ...]):
    """Return pinball loss for multi-quantile forecasts."""
    q = tf.constant(quantiles, dtype=tf.float32)
    def loss(y_true: tf.Tensor, y_pred: tf.Tensor) -> tf.Tensor:
        error = tf.expand_dims(y_true, -1) - y_pred
        return tf.reduce_mean(tf.maximum(q * error, (q - 1.0) * error))
    return loss


def build_tft(config: ModelConfig) -> tf.keras.Model:
    """Build a TFT using feature selection, LSTM temporal state, and attention."""
    inputs = tf.keras.Input((config.sequence_length, config.feature_count), name="dynamic_covariates")
    x = VariableSelectionNetwork(config.units, config.feature_count, name="variable_selection")(inputs)
    model_inputs: tf.Tensor | list[tf.Tensor] = inputs
    if config.static_feature_count:
        static = tf.keras.Input((config.static_feature_count,), name="static_covariates")
        context = tf.keras.layers.Dense(config.units, activation="elu", name="static_context")(static)
        context = tf.keras.layers.RepeatVector(config.sequence_length)(context)
        x = tf.keras.layers.Add()([x, context])
        model_inputs = [inputs, static]
    x = tf.keras.layers.LSTM(config.units, return_sequences=True)(x)
    attention = tf.keras.layers.MultiHeadAttention(num_heads=config.num_heads, key_dim=config.units // config.num_heads, name="temporal_attention")
    x = tf.keras.layers.Add()([x, attention(x, x)])
    x = tf.keras.layers.GlobalAveragePooling1D()(x)
    x = GatedResidualNetwork(config.units)(x)
    output = tf.keras.layers.Dense(len(config.quantiles), dtype="float32", name="quantile_forecast")(x)
    model = tf.keras.Model(model_inputs, output, name="temporal_fusion_transformer")
    model.compile(optimizer=tf.keras.optimizers.Adam(config.learning_rate), loss=quantile_loss(config.quantiles), metrics=["mae"])
    return model
