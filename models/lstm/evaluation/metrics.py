import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import math

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


class Metrics:
    """
    Regression Metrics Utility
    """

    # ======================================================
    # Mean Absolute Error
    # ======================================================

    @staticmethod
    def mae(
        y_true,
        y_pred,
    ):
        return mean_absolute_error(
            y_true,
            y_pred,
        )

    # ======================================================
    # Mean Squared Error
    # ======================================================

    @staticmethod
    def mse(
        y_true,
        y_pred,
    ):
        return mean_squared_error(
            y_true,
            y_pred,
        )

    # ======================================================
    # Root Mean Squared Error
    # ======================================================

    @staticmethod
    def rmse(
        y_true,
        y_pred,
    ):
        mse = mean_squared_error(
            y_true,
            y_pred,
        )

        return math.sqrt(
            mse
        )

    # ======================================================
    # R² Score
    # ======================================================

    @staticmethod
    def r2(
        y_true,
        y_pred,
    ):
        return r2_score(
            y_true,
            y_pred,
        )

    # ======================================================
    # Evaluate All Metrics
    # ======================================================

    @staticmethod
    def evaluate(
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

            "r2": Metrics.r2(
                y_true,
                y_pred,
            ),

        }