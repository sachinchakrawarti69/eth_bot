import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from pathlib import Path

import numpy as np
import tensorflow as tf

from models.lstm.datasets.dataset import LSTMDataset


# ==========================================================
# Predictor
# ==========================================================

class Predictor:

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
    # Predict Batch
    # ======================================================

    def predict(
        self,
        X,
    ):

        X = np.asarray(
            X,
            dtype=np.float32,
        )

        return self.model.predict(
            X,
            verbose=0,
        )

    # ======================================================
    # Predict One Sequence
    # ======================================================

    def predict_one(
        self,
        sequence,
    ):

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

        return float(
            prediction[0][0]
        )

    # ======================================================
    # Binary Signal
    # ======================================================

    def signal(
        self,
        value,
        threshold=0.5,
    ):

        if value >= threshold:
            return "BUY"

        return "SELL"

    # ======================================================
    # Predict With Signal
    # ======================================================

    def predict_with_signal(
        self,
        sequence,
    ):

        prediction = self.predict_one(
            sequence,
        )

        return {
            "prediction": prediction,
            "signal": self.signal(
                prediction,
            ),
        }


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("LSTM PREDICTION")
    print("=" * 70)

    dataset = LSTMDataset(
        sequence_length=60,
    )

    dataset.load()

    X_test, y_test = dataset.test()

    predictor = Predictor()

    print()

    print("Samples:", len(X_test))

    print()

    print("=" * 70)
    print("FIRST FIVE PREDICTIONS")
    print("=" * 70)

    predictions = predictor.predict(
        X_test[:5],
    )

    for i in range(5):

        prediction = float(
            predictions[i][0]
        )

        signal = predictor.signal(
            prediction,
        )

        print()

        print(f"Sample {i+1}")

        print(
            "Actual     :",
            float(y_test[i]),
        )

        print(
            "Prediction :",
            prediction,
        )

        print(
            "Signal     :",
            signal,
        )

    print()

    print("=" * 70)
    print("SINGLE PREDICTION")
    print("=" * 70)

    result = predictor.predict_with_signal(
        X_test[0],
    )

    print(result)

    print()

    print("=" * 70)
    print("PREDICTION COMPLETED")
    print("=" * 70)