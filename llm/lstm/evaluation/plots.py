import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from pathlib import Path

import matplotlib.pyplot as plt


class Plots:

    # ==========================================================
    # Prediction vs Actual
    # ==========================================================

    @staticmethod
    def prediction_plot(
        y_true,
        y_pred,
        save_path=None,
    ):

        plt.figure(figsize=(12, 5))

        plt.plot(
            y_true,
            label="Actual",
            linewidth=2,
        )

        plt.plot(
            y_pred,
            label="Prediction",
            linewidth=2,
        )

        plt.title("Prediction vs Actual")

        plt.xlabel("Samples")

        plt.ylabel("Value")

        plt.grid(True)

        plt.legend()

        plt.tight_layout()

        if save_path:

            save_path = Path(save_path)

            save_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            plt.savefig(save_path)

            print("Saved:", save_path)

        plt.close()

    # ==========================================================
    # Loss Curve
    # ==========================================================

    @staticmethod
    def loss_curve(
        history,
        save_path=None,
    ):

        plt.figure(figsize=(10, 5))

        plt.plot(
            history.history["loss"],
            label="Train Loss",
        )

        if "val_loss" in history.history:

            plt.plot(
                history.history["val_loss"],
                label="Validation Loss",
            )

        plt.title("Loss Curve")

        plt.xlabel("Epoch")

        plt.ylabel("Loss")

        plt.grid(True)

        plt.legend()

        plt.tight_layout()

        if save_path:

            save_path = Path(save_path)

            save_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            plt.savefig(save_path)

            print("Saved:", save_path)

        plt.close()

    # ==========================================================
    # MAE Curve
    # ==========================================================

    @staticmethod
    def mae_curve(
        history,
        save_path=None,
    ):

        plt.figure(figsize=(10, 5))

        plt.plot(
            history.history["mae"],
            label="Train MAE",
        )

        if "val_mae" in history.history:

            plt.plot(
                history.history["val_mae"],
                label="Validation MAE",
            )

        plt.title("MAE Curve")

        plt.xlabel("Epoch")

        plt.ylabel("MAE")

        plt.grid(True)

        plt.legend()

        plt.tight_layout()

        if save_path:

            save_path = Path(save_path)

            save_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            plt.savefig(save_path)

            print("Saved:", save_path)

        plt.close()

    # ==========================================================
    # Scatter Plot
    # ==========================================================

    @staticmethod
    def scatter_plot(
        y_true,
        y_pred,
        save_path=None,
    ):

        plt.figure(figsize=(6, 6))

        plt.scatter(
            y_true,
            y_pred,
            alpha=0.7,
        )

        plt.xlabel("Actual")

        plt.ylabel("Prediction")

        plt.title("Actual vs Prediction")

        plt.grid(True)

        plt.tight_layout()

        if save_path:

            save_path = Path(save_path)

            save_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            plt.savefig(save_path)

            print("Saved:", save_path)

        plt.close()