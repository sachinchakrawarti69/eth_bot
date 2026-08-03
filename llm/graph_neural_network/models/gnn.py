"""Graph convolution and graph-attention models for related crypto assets."""
from __future__ import annotations
import tensorflow as tf
from llm.shared import ModelConfig


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class GraphConvolution(tf.keras.layers.Layer):
    """Aggregates normalized neighbouring asset features using an adjacency matrix."""
    def __init__(self, units: int, activation: str = "relu", **kwargs: object) -> None:
        super().__init__(**kwargs); self.units, self.activation = units, activation; self.projection = tf.keras.layers.Dense(units, use_bias=False)
    def call(self, inputs: tuple[tf.Tensor, tf.Tensor]) -> tf.Tensor:
        features, adjacency = inputs; identity = tf.eye(tf.shape(adjacency)[-1], batch_shape=[tf.shape(adjacency)[0]])
        adjacency = adjacency + identity; degree = tf.reduce_sum(adjacency, axis=-1, keepdims=True)
        return tf.keras.activations.get(self.activation)(tf.matmul(adjacency / tf.maximum(degree, 1e-7), self.projection(features)))
    def get_config(self) -> dict[str, object]: return {**super().get_config(), "units": self.units, "activation": self.activation}


@tf.keras.utils.register_keras_serializable(package="eth_bot")
class GraphAttention(tf.keras.layers.Layer):
    """Learns attention weights for each edge rather than treating edges equally."""
    def __init__(self, units: int, **kwargs: object) -> None:
        super().__init__(**kwargs); self.units = units; self.query = tf.keras.layers.Dense(units); self.key = tf.keras.layers.Dense(units); self.value = tf.keras.layers.Dense(units)
    def call(self, inputs: tuple[tf.Tensor, tf.Tensor]) -> tf.Tensor:
        features, adjacency = inputs; q, k, v = self.query(features), self.key(features), self.value(features)
        scores = tf.matmul(q, k, transpose_b=True) / tf.math.sqrt(tf.cast(self.units, tf.float32))
        scores = tf.where(adjacency > 0, scores, tf.cast(-1e9, scores.dtype))
        return tf.matmul(tf.nn.softmax(scores, axis=-1), v)
    def get_config(self) -> dict[str, object]: return {**super().get_config(), "units": self.units}


def build_gnn(config: ModelConfig, node_count: int) -> tf.keras.Model:
    """Build an asset graph regressor with node and edge (adjacency) inputs."""
    if node_count < 1: raise ValueError("node_count must be positive")
    nodes = tf.keras.Input((node_count, config.feature_count), name="node_features")
    edges = tf.keras.Input((node_count, node_count), name="edge_features")
    x = GraphConvolution(config.units)([nodes, edges]); x = GraphAttention(config.units)([x, edges])
    x = tf.keras.layers.GlobalAveragePooling1D()(x); output = tf.keras.layers.Dense(config.output_units, dtype="float32")(x)
    model = tf.keras.Model([nodes, edges], output, name="asset_gnn"); model.compile(optimizer=tf.keras.optimizers.Adam(config.learning_rate), loss="mse", metrics=["mae"])
    return model
