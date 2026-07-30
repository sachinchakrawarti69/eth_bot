import numpy as np


# ==========================================================
# Sequence Dataset
# ==========================================================

class SequenceDataset:

    def __init__(self, X, y):

        self.X = np.asarray(X, dtype=np.float32)
        self.y = np.asarray(y, dtype=np.float32)

        if len(self.X) != len(self.y):
            raise ValueError("X and y must have the same number of samples.")

    # ======================================================
    # Dataset Length
    # ======================================================

    def __len__(self):

        return len(self.X)

    # ======================================================
    # Get One Sample
    # ======================================================

    def __getitem__(self, index):

        return self.X[index], self.y[index]

    # ======================================================
    # Input Shape
    # ======================================================

    @property
    def input_shape(self):

        return self.X.shape[1:]

    # ======================================================
    # Number of Features
    # ======================================================

    @property
    def feature_count(self):

        return self.X.shape[2]

    # ======================================================
    # Sequence Length
    # ======================================================

    @property
    def sequence_length(self):

        return self.X.shape[1]

    # ======================================================
    # Summary
    # ======================================================

    def summary(self):

        print("=" * 70)
        print("SEQUENCE DATASET")
        print("=" * 70)

        print()

        print("Samples :", len(self))

        print("Timesteps :", self.sequence_length)

        print("Features :", self.feature_count)

        print()

        print("Input Shape :", self.input_shape)

        print("Target Shape :", self.y.shape)

    # ======================================================
    # First Sample
    # ======================================================

    def first(self):

        return self[0]

    # ======================================================
    # Last Sample
    # ======================================================

    def last(self):

        return self[-1]