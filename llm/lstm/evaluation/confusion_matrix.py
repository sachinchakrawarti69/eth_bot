import numpy as np

from sklearn.metrics import (
    confusion_matrix,
    ConfusionMatrixDisplay,
)

import matplotlib.pyplot as plt


class ConfusionMatrix:

    # ==========================================================
    # Compute Confusion Matrix
    # ==========================================================

    @staticmethod
    def compute(
        y_true,
        y_pred,
    ):

        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        return confusion_matrix(
            y_true,
            y_pred,
        )

    # ==========================================================
    # Display
    # ==========================================================

    @staticmethod
    def display(
        y_true,
        y_pred,
        labels=None,
        cmap="Blues",
    ):

        cm = ConfusionMatrix.compute(
            y_true,
            y_pred,
        )

        disp = ConfusionMatrixDisplay(
            confusion_matrix=cm,
            display_labels=labels,
        )

        disp.plot(cmap=cmap)

        plt.title("Confusion Matrix")
        plt.tight_layout()
        plt.show()

        return cm

    # ==========================================================
    # Print
    # ==========================================================

    @staticmethod
    def print(
        y_true,
        y_pred,
    ):

        cm = ConfusionMatrix.compute(
            y_true,
            y_pred,
        )

        print(cm)

        return cm