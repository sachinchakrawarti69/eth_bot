"""Keras GRU architectures for candle forecasting."""
from __future__ import annotations

import tensorflow as tf

from models.shared import ModelConfig


def _compile(model: tf.keras.Model, config: ModelConfig) -> tf.keras.Model:
    model.compile(optimizer=tf.keras.optimizers.Adam(config.learning_rate), loss="mse", metrics=["mae"])
    return model


def build_gru(config: ModelConfig) -> tf.keras.Model:
    """Build a single-GRU regressor accepting (time, features) sequences."""
    inputs = tf.keras.Input((config.sequence_length, config.feature_count))
    x = tf.keras.layers.GRU(config.units, dropout=config.dropout)(inputs)
    output = tf.keras.layers.Dense(config.output_units, dtype="float32")(x)
    return _compile(tf.keras.Model(inputs, output, name="single_gru"), config)


def build_stacked_gru(config: ModelConfig) -> tf.keras.Model:
    """Build a two-layer GRU that learns hierarchical temporal features."""
    inputs = tf.keras.Input((config.sequence_length, config.feature_count))
    x = tf.keras.layers.GRU(config.units, return_sequences=True, dropout=config.dropout)(inputs)
    x = tf.keras.layers.GRU(config.units // 2, dropout=config.dropout)(x)
    return _compile(tf.keras.Model(inputs, tf.keras.layers.Dense(config.output_units, dtype="float32")(x), name="stacked_gru"), config)


def build_bidirectional_gru(config: ModelConfig) -> tf.keras.Model:
    """Build a bidirectional GRU for offline windows where future context is allowed."""
    inputs = tf.keras.Input((config.sequence_length, config.feature_count))
    x = tf.keras.layers.Bidirectional(tf.keras.layers.GRU(config.units, dropout=config.dropout))(inputs)
    return _compile(tf.keras.Model(inputs, tf.keras.layers.Dense(config.output_units, dtype="float32")(x), name="bidirectional_gru"), config)


def build_attention_gru(config: ModelConfig) -> tf.keras.Model:
    """Build a GRU with learnable additive attention over time steps."""
    inputs = tf.keras.Input((config.sequence_length, config.feature_count))
    states = tf.keras.layers.GRU(config.units, return_sequences=True, dropout=config.dropout)(inputs)
    scores = tf.keras.layers.Dense(1, activation="tanh")(states)
    weights = tf.keras.layers.Softmax(axis=1, name="temporal_attention")(scores)
    context = tf.keras.layers.Lambda(lambda tensors: tf.reduce_sum(tensors[0] * tensors[1], axis=1))([states, weights])
    return _compile(tf.keras.Model(inputs, tf.keras.layers.Dense(config.output_units, dtype="float32")(context), name="attention_gru"), config)
