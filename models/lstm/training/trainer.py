import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf

from pathlib import Path

from tensorflow.keras.callbacks import (

    EarlyStopping,

    ModelCheckpoint,

    ReduceLROnPlateau,

)


# ==========================================================
# Trainer
# ==========================================================

class Trainer:

    def __init__(

        self,

        model,

        save_dir="storage/models",

    ):

        self.model = model

        self.save_dir = Path(save_dir)

        self.save_dir.mkdir(

            parents=True,

            exist_ok=True,

        )

    # ======================================================
    # Callbacks
    # ======================================================

    def callbacks(self):

        checkpoint = ModelCheckpoint(

            filepath=str(

                self.save_dir / "best_model.keras"

            ),

            monitor="val_loss",

            save_best_only=True,

            verbose=1,

        )

        early = EarlyStopping(

            monitor="val_loss",

            patience=10,

            restore_best_weights=True,

            verbose=1,

        )

        reduce_lr = ReduceLROnPlateau(

            monitor="val_loss",

            factor=0.5,

            patience=5,

            verbose=1,

        )

        return [

            checkpoint,

            early,

            reduce_lr,

        ]

    # ======================================================
    # Train
    # ======================================================

    def train(

        self,

        X_train,

        y_train,

        X_validation,

        y_validation,

        epochs=5,

        batch_size=32,

    ):

        history = self.model.fit(

            X_train,

            y_train,

            validation_data=(

                X_validation,

                y_validation,

            ),

            epochs=epochs,

            batch_size=batch_size,

            callbacks=self.callbacks(),

            verbose=1,

        )

        return history

    # ======================================================
    # Evaluate
    # ======================================================

    def evaluate(

        self,

        X_test,

        y_test,

    ):

        return self.model.evaluate(

            X_test,

            y_test,

            verbose=1,

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
    # Save
    # ======================================================

    def save(

        self,

        filename="final_model.keras",

    ):

        path = self.save_dir / filename

        self.model.save(path)

        print()

        print("Saved:", path)

    # ======================================================
    # Summary
    # ======================================================

    def summary(self):

        self.model.summary()