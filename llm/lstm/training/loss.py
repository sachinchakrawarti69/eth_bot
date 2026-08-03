import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from tensorflow.keras.losses import (
    MeanSquaredError,
    MeanAbsoluteError,
    BinaryCrossentropy,
    CategoricalCrossentropy,
    Huber,
)


class LossFactory:
    """
    Loss function factory.
    """

    @staticmethod
    def get(name="mse"):

        name = name.lower()

        losses = {
            "mse": MeanSquaredError(),
            "mae": MeanAbsoluteError(),
            "binary_crossentropy": BinaryCrossentropy(),
            "categorical_crossentropy": CategoricalCrossentropy(),
            "huber": Huber(),
        }

        if name not in losses:
            raise ValueError(
                f"Unknown loss function: {name}"
            )

        return losses[name]