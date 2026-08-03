"""Reusable training, preprocessing, inference, and metric utilities.

The functions in this module deliberately know nothing about a particular neural
architecture.  Individual packages own their model graph and import these
small, testable services.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import tensorflow as tf
from sklearn.metrics import (confusion_matrix, f1_score, mean_absolute_error,
                             mean_absolute_percentage_error, mean_squared_error,
                             precision_score, r2_score, recall_score, roc_curve)
from sklearn.preprocessing import StandardScaler

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelConfig:
    """Validated common settings for a sequence forecasting model.

    Attributes:
        sequence_length: Number of historical candles in one sample.
        feature_count: Number of features at each time step.
        output_units: Number of scalar targets per sample.
        learning_rate: Adam learning rate.
        dropout: Dropout probability.
    """

    sequence_length: int = 60
    feature_count: int = 11
    output_units: int = 1
    learning_rate: float = 1e-3
    dropout: float = 0.2
    units: int = 64
    num_heads: int = 4
    quantiles: tuple[float, ...] = (0.1, 0.5, 0.9)
    static_feature_count: int = 0

    def __post_init__(self) -> None:
        if min(self.sequence_length, self.feature_count, self.output_units, self.units) < 1 or self.static_feature_count < 0:
            raise ValueError("sequence_length, feature_count, output_units, and units must be positive")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")


class SequencePreprocessor:
    """Fits a scaler and turns tabular candles into supervised sequences."""

    def __init__(self) -> None:
        self.scaler = StandardScaler()
        self._fitted = False

    def fit_transform(self, values: np.ndarray) -> np.ndarray:
        """Fit on a two-dimensional feature matrix and return scaled values."""
        array = self._validate_matrix(values)
        self._fitted = True
        return self.scaler.fit_transform(array)

    def transform(self, values: np.ndarray) -> np.ndarray:
        """Scale values with the fitted training-set statistics."""
        if not self._fitted:
            raise RuntimeError("SequencePreprocessor must be fitted before transform")
        return self.scaler.transform(self._validate_matrix(values))

    def create_sequences(
        self, values: np.ndarray, sequence_length: int, target_index: int = 0
    ) -> tuple[np.ndarray, np.ndarray]:
        """Create samples whose target is the candle immediately after each window."""
        array = self._validate_matrix(values)
        if sequence_length >= len(array):
            raise ValueError("sequence_length must be smaller than number of rows")
        if not 0 <= target_index < array.shape[1]:
            raise ValueError("target_index is outside feature columns")
        x = np.asarray([array[i:i + sequence_length] for i in range(len(array) - sequence_length)])
        y = array[sequence_length:, target_index]
        return x.astype(np.float32), y.astype(np.float32)

    @staticmethod
    def _validate_matrix(values: np.ndarray) -> np.ndarray:
        array = np.asarray(values, dtype=np.float32)
        if array.ndim != 2 or array.shape[0] < 2:
            raise ValueError("values must be a two-dimensional matrix with at least two rows")
        return array


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Calculate standard regression metrics with stable one-dimensional inputs."""
    truth, prediction = np.ravel(y_true), np.ravel(y_pred)
    return {
        "mae": float(mean_absolute_error(truth, prediction)),
        "mse": float(mean_squared_error(truth, prediction)),
        "rmse": float(mean_squared_error(truth, prediction) ** 0.5),
        "mape": float(mean_absolute_percentage_error(truth, prediction)),
        "r2": float(r2_score(truth, prediction)),
    }


def classification_metrics(y_true: np.ndarray, y_score: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    """Calculate precision, recall, and F1 for probabilistic binary predictions."""
    truth = np.ravel(y_true).astype(int)
    prediction = (np.ravel(y_score) >= threshold).astype(int)
    return {
        "precision": float(precision_score(truth, prediction, zero_division=0)),
        "recall": float(recall_score(truth, prediction, zero_division=0)),
        "f1": float(f1_score(truth, prediction, zero_division=0)),
    }


def classification_diagnostics(y_true: np.ndarray, y_score: np.ndarray, threshold: float = 0.5) -> dict[str, np.ndarray]:
    """Return confusion-matrix and ROC points for binary trading-direction models."""
    truth = np.ravel(y_true).astype(int)
    score = np.ravel(y_score)
    false_positive_rate, true_positive_rate, thresholds = roc_curve(truth, score)
    return {
        "confusion_matrix": confusion_matrix(truth, (score >= threshold).astype(int)),
        "false_positive_rate": false_positive_rate,
        "true_positive_rate": true_positive_rate,
        "thresholds": thresholds,
    }


class Trainer:
    """Keras trainer providing checkpoints, TensorBoard, mixed precision, and resume."""

    def __init__(self, model: tf.keras.Model, run_dir: str | Path, mixed_precision: bool = False) -> None:
        self.model = model
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        if mixed_precision and tf.config.list_physical_devices("GPU"):
            tf.keras.mixed_precision.set_global_policy("mixed_float16")
            LOGGER.info("Enabled mixed_float16 policy")

    @staticmethod
    def gpu_available() -> bool:
        """Return whether TensorFlow can see a GPU."""
        return bool(tf.config.list_physical_devices("GPU"))

    def fit(
        self, x_train: np.ndarray, y_train: np.ndarray, x_validation: np.ndarray,
        y_validation: np.ndarray, epochs: int = 50, batch_size: int = 32,
        resume: bool = False,
    ) -> tf.keras.callbacks.History:
        """Train the model and optionally resume from the best saved checkpoint."""
        checkpoint = self.run_dir / "best_model.keras"
        if resume and checkpoint.exists():
            self.model = tf.keras.models.load_model(checkpoint)
            LOGGER.info("Resumed model from %s", checkpoint)
        callbacks: list[tf.keras.callbacks.Callback] = [
            tf.keras.callbacks.ModelCheckpoint(checkpoint, monitor="val_loss", save_best_only=True),
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", patience=5, factor=0.5),
            tf.keras.callbacks.TensorBoard(log_dir=str(self.run_dir / "tensorboard")),
        ]
        return self.model.fit(x_train, y_train, validation_data=(x_validation, y_validation),
                              epochs=epochs, batch_size=batch_size, callbacks=callbacks, verbose=2)


def predict_batch(model: tf.keras.Model, samples: np.ndarray) -> np.ndarray:
    """Validate a batch of sequence samples and return NumPy predictions."""
    array = np.asarray(samples, dtype=np.float32)
    if array.ndim not in (3, 4):
        raise ValueError("samples must have shape (batch, time, features) or graph equivalent")
    return model.predict(array, verbose=0)


def train_from_numpy(
    builder: Any, config: ModelConfig, data_dir: str | Path, run_dir: str | Path,
    *, resume: bool = False, mixed_precision: bool = True,
) -> tf.keras.callbacks.History:
    """Train a model builder against the standard four-file NumPy dataset contract."""
    directory = Path(data_dir)
    required = ("x_train.npy", "y_train.npy", "x_validation.npy", "y_validation.npy")
    missing = [name for name in required if not (directory / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing training arrays: {', '.join(missing)}")
    return Trainer(builder(config), run_dir, mixed_precision=mixed_precision).fit(
        *(np.load(directory / name) for name in required), resume=resume
    )
