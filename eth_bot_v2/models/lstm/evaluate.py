import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from pathlib import Path

import numpy as np
import tensorflow as tf

from models.lstm.datasets.dataset import LSTMDataset
from models.lstm.evaluation.metrics import Metrics
from models.lstm.evaluation.classification_metrics import ClassificationMetrics
from models.lstm.evaluation.regression_metrics import RegressionMetrics
from models.lstm.evaluation.confusion_matrix import ConfusionMatrix
from models.lstm.evaluation.roc_curve import ROCCurve
from models.lstm.evaluation.report import EvaluationReport


# ==========================================================
# Model Evaluator
# ==========================================================

class Evaluator:

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

        return self.model.predict(
            X,
            verbose=0,
        )

    # ======================================================
    # Regression Evaluation
    # ======================================================

    def evaluate_regression(
        self,
        y_true,
        y_pred,
    ):

        return {

            "mae": Metrics.mae(
                y_true,
                y_pred,
            ),

            "mse": Metrics.mse(
                y_true,
                y_pred,
            ),

            "rmse": Metrics.rmse(
                y_true,
                y_pred,
            ),

            "r2": RegressionMetrics.r2_score(
                y_true,
                y_pred,
            ),
        }

    # ======================================================
    # Classification Evaluation
    # ======================================================

    def evaluate_classification(
        self,
        y_true,
        y_pred,
    ):

        y_true = np.asarray(y_true).flatten()

        y_pred = np.asarray(y_pred).flatten()

        y_true = (y_true > 0.5).astype(int)

        y_pred = (y_pred > 0.5).astype(int)

        return {

            "accuracy": ClassificationMetrics.accuracy(
                y_true,
                y_pred,
            ),

            "precision": ClassificationMetrics.precision(
                y_true,
                y_pred,
            ),

            "recall": ClassificationMetrics.recall(
                y_true,
                y_pred,
            ),

            "f1": ClassificationMetrics.f1(
                y_true,
                y_pred,
            ),
        }


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)

    dataset = LSTMDataset(
        sequence_length=60,
    )

    dataset.load()

    X_test, y_test = dataset.test()

    print()

    print("Test Samples :", len(X_test))

    evaluator = Evaluator()

    predictions = evaluator.predict(
        X_test,
    )

    print()

    print("=" * 70)
    print("REGRESSION METRICS")
    print("=" * 70)

    regression = evaluator.evaluate_regression(
        y_test,
        predictions,
    )

    for key, value in regression.items():
        print(f"{key:<10}: {value:.6f}")

    print()

    print("=" * 70)
    print("CLASSIFICATION METRICS")
    print("=" * 70)

    classification = evaluator.evaluate_classification(
        y_test,
        predictions,
    )

    for key, value in classification.items():
        print(f"{key:<10}: {value:.6f}")

    print()

    print("=" * 70)
    print("GENERATING REPORTS")
    print("=" * 70)

    ConfusionMatrix.plot(
        (y_test > 0.5).astype(int),
        (predictions > 0.5).astype(int),
        save_path="storage/reports/confusion_matrix.png",
    )

    ROCCurve.plot(
        (y_test > 0.5).astype(int),
        predictions.flatten(),
        save_path="storage/reports/roc_curve.png",
    )

    report = EvaluationReport()

    report.save_json(
        {
            "regression": regression,
            "classification": classification,
        },
        "storage/reports/evaluation_report.json",
    )

    print()

    print("Saved:")
    print("storage/reports/confusion_matrix.png")
    print("storage/reports/roc_curve.png")
    print("storage/reports/evaluation_report.json")

    print()

    print("=" * 70)
    print("EVALUATION COMPLETED")
    print("=" * 70)