import math
import numpy as np

from llm.lstm.datasets.dataset import LSTMDataset


# ==========================================================
# LSTM DataLoader
# ==========================================================

class LSTMDataLoader:

    def __init__(
        self,
        batch_size=32,
        sequence_length=60,
        target_column="close",
        normalize_method="standard",
    ):

        self.batch_size = batch_size

        self.dataset = LSTMDataset(
            sequence_length=sequence_length,
            target_column=target_column,
            normalize_method=normalize_method,
        )

        self.dataset.load()

    # ======================================================
    # Batch Generator
    # ======================================================

    def batch_generator(self, X, y):

        total = len(X)

        for start in range(0, total, self.batch_size):

            end = start + self.batch_size

            yield X[start:end], y[start:end]

    # ======================================================
    # Train Loader
    # ======================================================

    def train_loader(self):

        X, y = self.dataset.train()

        return self.batch_generator(X, y)

    # ======================================================
    # Validation Loader
    # ======================================================

    def validation_loader(self):

        X, y = self.dataset.validation()

        return self.batch_generator(X, y)

    # ======================================================
    # Test Loader
    # ======================================================

    def test_loader(self):

        X, y = self.dataset.test()

        return self.batch_generator(X, y)

    # ======================================================
    # Statistics
    # ======================================================

    def summary(self):

        X_train, y_train = self.dataset.train()

        X_validation, y_validation = self.dataset.validation()

        X_test, y_test = self.dataset.test()

        print("=" * 70)
        print("LSTM DATALOADER")
        print("=" * 70)

        print()

        print("Batch Size :", self.batch_size)

        print()

        print("Train Samples :", len(X_train))

        print("Validation Samples :", len(X_validation))

        print("Test Samples :", len(X_test))

        print()

        print(
            "Train Batches :",
            math.ceil(len(X_train) / self.batch_size),
        )

        print(
            "Validation Batches :",
            math.ceil(len(X_validation) / self.batch_size),
        )

        print(
            "Test Batches :",
            math.ceil(len(X_test) / self.batch_size),
        )

        print()

        print("Input Shape :", self.dataset.input_shape())