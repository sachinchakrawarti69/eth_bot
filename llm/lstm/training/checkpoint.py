import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from pathlib import Path

from tensorflow.keras.callbacks import (
    ModelCheckpoint,
)


class CheckpointFactory:
    """
    Model checkpoint callback factory.
    """

    @staticmethod
    def best_model(
        save_dir="storage/models",
        filename="best_model.keras",
        monitor="val_loss",
        save_best_only=True,
        verbose=1,
    ):

        save_dir = Path(save_dir)

        save_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return ModelCheckpoint(
            filepath=str(
                save_dir / filename
            ),
            monitor=monitor,
            save_best_only=save_best_only,
            verbose=verbose,
        )

    @staticmethod
    def get(
        **kwargs,
    ):
        return CheckpointFactory.best_model(
            **kwargs,
        )