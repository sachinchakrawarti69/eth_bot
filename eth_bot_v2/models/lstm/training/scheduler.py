import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from tensorflow.keras.callbacks import (
    ReduceLROnPlateau,
)


class SchedulerFactory:
    """
    Learning rate scheduler factory.
    """

    @staticmethod
    def reduce_lr_on_plateau(
        monitor="val_loss",
        factor=0.5,
        patience=5,
        min_lr=1e-6,
        verbose=1,
    ):
        return ReduceLROnPlateau(
            monitor=monitor,
            factor=factor,
            patience=patience,
            min_lr=min_lr,
            verbose=verbose,
        )

    @staticmethod
    def get(
        name="reduce_lr_on_plateau",
        **kwargs,
    ):

        name = name.lower()

        if name == "reduce_lr_on_plateau":
            return SchedulerFactory.reduce_lr_on_plateau(
                **kwargs,
            )

        raise ValueError(
            f"Unknown scheduler: {name}"
        )