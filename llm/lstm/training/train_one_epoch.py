import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


def train_one_epoch(
    model,
    X_train,
    y_train,
    X_validation,
    y_validation,
    batch_size=32,
):
    """
    Train the model for exactly one epoch.
    """

    history = model.fit(
        X_train,
        y_train,
        validation_data=(
            X_validation,
            y_validation,
        ),
        epochs=1,
        batch_size=batch_size,
        verbose=1,
    )

    return history