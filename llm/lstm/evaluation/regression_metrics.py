from math import sqrt

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


class RegressionMetrics:
    """
    Regression evaluation metrics.
    """

    # ==========================================================
    # MAE
    # ==========================================================

    @staticmethod
    def mae(
        y_true,
        y_pred,
    ):
        return mean_absolute_error(
            y_true,
            y_pred,
        )

    # ==========================================================
    # MSE
    # ==========================================================

    @staticmethod
    def mse(
        y_true,
        y_pred,
    ):
        return mean_squared_error(
            y_true,
            y_pred,
        )

    # ==========================================================
    # RMSE
    # ==========================================================

    @staticmethod
    def rmse(
        y_true,
        y_pred,
    ):
        mse = mean_squared_error(
            y_true,
            y_pred,
        )

        return sqrt(mse)

    # ==========================================================
    # R2
    # ==========================================================

    @staticmethod
    def r2(
        y_true,
        y_pred,
    ):
        return r2_score(
            y_true,
            y_pred,
        )

    # ==========================================================
    # All Metrics
    # ==========================================================

    @staticmethod
    def evaluate(
        y_true,
        y_pred,
    ):
        return {
            "mae": RegressionMetrics.mae(
                y_true,
                y_pred,
            ),
            "mse": RegressionMetrics.mse(
                y_true,
                y_pred,
            ),
            "rmse": RegressionMetrics.rmse(
                y_true,
                y_pred,
            ),
            "r2": RegressionMetrics.r2(
                y_true,
                y_pred,
            ),
        }