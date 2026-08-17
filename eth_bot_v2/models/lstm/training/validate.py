import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


class Validator:
    """
    Validation helper for TensorFlow/Keras models.
    """

    def __init__(self, model):
        self.model = model

    def validate(
        self,
        X_validation,
        y_validation,
        batch_size=32,
    ):
        """
        Evaluate the model on validation data.
        """

        loss, mae = self.model.evaluate(
            X_validation,
            y_validation,
            batch_size=batch_size,
            verbose=1,
        )

        return {
            "loss": loss,
            "mae": mae,
        }