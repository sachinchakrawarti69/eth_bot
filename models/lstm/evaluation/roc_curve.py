import matplotlib.pyplot as plt

from sklearn.metrics import (
    roc_curve,
    auc,
)


class ROCCurve:

    @staticmethod
    def compute(
        y_true,
        y_score,
    ):
        """
        Returns:
            fpr
            tpr
            thresholds
            roc_auc
        """

        fpr, tpr, thresholds = roc_curve(
            y_true,
            y_score,
        )

        roc_auc = auc(
            fpr,
            tpr,
        )

        return (
            fpr,
            tpr,
            thresholds,
            roc_auc,
        )

    @staticmethod
    def plot(
        y_true,
        y_score,
        save_path=None,
        show=False,
    ):
        """
        Plot ROC Curve
        """

        (
            fpr,
            tpr,
            _,
            roc_auc,
        ) = ROCCurve.compute(
            y_true,
            y_score,
        )

        plt.figure(figsize=(8, 6))

        plt.plot(
            fpr,
            tpr,
            linewidth=2,
            label=f"AUC = {roc_auc:.4f}",
        )

        plt.plot(
            [0, 1],
            [0, 1],
            linestyle="--",
        )

        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve")
        plt.legend()
        plt.grid(True)

        if save_path is not None:
            plt.savefig(
                save_path,
                dpi=200,
                bbox_inches="tight",
            )

        if show:
            plt.show()

        plt.close()

        return roc_auc