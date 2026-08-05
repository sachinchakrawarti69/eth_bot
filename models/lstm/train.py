import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from models.lstm.datasets.dataset import LSTMDataset
from models.lstm.models.lstm_model import build_lstm_model
from models.lstm.training.trainer import Trainer


# ==========================================================
# Main Training Script
# ==========================================================

def main():

    print("=" * 70)
    print("LSTM MODEL TRAINING")
    print("=" * 70)

    # ------------------------------------------------------
    # Dataset
    # ------------------------------------------------------

    print()
    print("Loading dataset...")

    dataset = LSTMDataset(
        sequence_length=60,
    )

    dataset.load()

    X_train, y_train = dataset.train()

    X_validation, y_validation = dataset.validation()

    X_test, y_test = dataset.test()

    print("Done")

    print()

    print("Train Shape")
    print(X_train.shape)
    print(y_train.shape)

    print()

    print("Validation Shape")
    print(X_validation.shape)
    print(y_validation.shape)

    print()

    print("Test Shape")
    print(X_test.shape)
    print(y_test.shape)

    # ------------------------------------------------------
    # Build Model
    # ------------------------------------------------------

    print()
    print("=" * 70)
    print("BUILD MODEL")
    print("=" * 70)

    model = build_lstm_model(
        input_shape=dataset.input_shape(),
    )

    model.summary()

    # ------------------------------------------------------
    # Trainer
    # ------------------------------------------------------

    trainer = Trainer(
        model=model,
    )

    # ------------------------------------------------------
    # Train
    # ------------------------------------------------------

    print()
    print("=" * 70)
    print("TRAINING")
    print("=" * 70)

    history = trainer.train(
        X_train,
        y_train,
        X_validation,
        y_validation,
        epochs=50,
        batch_size=32,
    )

    # ------------------------------------------------------
    # Evaluate
    # ------------------------------------------------------

    print()
    print("=" * 70)
    print("EVALUATION")
    print("=" * 70)

    loss, mae = trainer.evaluate(
        X_test,
        y_test,
    )

    print()

    print(f"Loss : {loss:.6f}")
    print(f"MAE  : {mae:.6f}")

    # ------------------------------------------------------
    # Save
    # ------------------------------------------------------

    print()
    print("=" * 70)
    print("SAVE MODEL")
    print("=" * 70)

    trainer.save()

    print()

    print("Best Model : storage/models/best_model.keras")
    print("Final Model: storage/models/final_model.keras")

    print()

    print("=" * 70)
    print("TRAINING COMPLETED")
    print("=" * 70)

    return history


# ==========================================================
# Run
# ==========================================================

if __name__ == "__main__":
    main()