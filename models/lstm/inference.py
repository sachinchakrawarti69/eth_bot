import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from pathlib import Path

import numpy as np
import tensorflow as tf


class LSTMInference:
    """
    Loads a trained LSTM model and performs inference.
    """

    def __init__(
        self,
        model_path="storage/models/final_model.keras",
    ):
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}"
            )

        self.model = tf.keras.models.load_model(
            self.model_path
        )

    # ======================================================
    # Predict
    # ======================================================

    def predict(
        self,
        X,
    ):
        """
        Predict for one or many sequences.

        Shape:
            (samples, sequence_length, features)
        """

        X = np.asarray(
            X,
            dtype=np.float32,
        )

        return self.model.predict(
            X,
            verbose=0,
        )

    # ======================================================
    # Predict Single Sequence
    # ======================================================

    def predict_one(
        self,
        sequence,
    ):
        """
        Shape:
            (sequence_length, features)
        """

        sequence = np.asarray(
            sequence,
            dtype=np.float32,
        )

        sequence = np.expand_dims(
            sequence,
            axis=0,
        )

        prediction = self.model.predict(
            sequence,
            verbose=0,
        )

        return float(prediction[0][0])

    # ======================================================
    # Summary
    # ======================================================

    def summary(self):
        self.model.summary()


# ==========================================================
# Example
# ==========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("LSTM INFERENCE")
    print("=" * 70)

    predictor = LSTMInference()

    predictor.summary()

    dummy = np.random.rand(
        1,
        60,
        11,
    ).astype(np.float32)

    prediction = predictor.predict(dummy)

    print()
    print("Prediction")
    print(prediction)