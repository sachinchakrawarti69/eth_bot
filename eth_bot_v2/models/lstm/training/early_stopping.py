import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from tensorflow.keras.callbacks import (
    EarlyStopping,
)


class EarlyStoppingFactory:
    """
    EarlyStopping callback factory.
    """

    @staticmethod
    def default(
        monitor="val_loss",
        patience=10,
        restore_best_weights=True,
        verbose=1,
    ):
        return EarlyStopping(
            monitor=monitor,
            patience=patience,
            restore_best_weights=restore_best_weights,
            verbose=verbose,
        )

    @staticmethod
    def get(
        **kwargs,
    ):
        return EarlyStoppingFactory.default(
            **kwargs,
        )