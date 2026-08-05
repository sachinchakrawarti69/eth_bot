import numpy as np


# ==========================================================
# Split Dataset
# ==========================================================

def split_dataset(
    X,
    y,
    train_ratio=0.70,
    validation_ratio=0.15,
):
    """
    Time-series split.

    Returns

    X_train
    X_validation
    X_test

    y_train
    y_validation
    y_test
    """

    total = len(X)

    train_end = int(total * train_ratio)

    validation_end = train_end + int(total * validation_ratio)

    X_train = X[:train_end]
    y_train = y[:train_end]

    X_validation = X[train_end:validation_end]
    y_validation = y[train_end:validation_end]

    X_test = X[validation_end:]
    y_test = y[validation_end:]

    return (
        X_train,
        X_validation,
        X_test,
        y_train,
        y_validation,
        y_test,
    )


# ==========================================================
# Print Split Summary
# ==========================================================

def print_dataset_summary(
    X_train,
    X_validation,
    X_test,
    y_train,
    y_validation,
    y_test,
):

    print("=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)

    print()

    print("TRAIN")
    print("X :", X_train.shape)
    print("y :", y_train.shape)

    print()

    print("VALIDATION")
    print("X :", X_validation.shape)
    print("y :", y_validation.shape)

    print()

    print("TEST")
    print("X :", X_test.shape)
    print("y :", y_test.shape)

    print()

    print("Total Samples")

    print(
        len(X_train)
        + len(X_validation)
        + len(X_test)
    )


# ==========================================================
# Verify Split
# ==========================================================

def verify_split(
    X_train,
    X_validation,
    X_test,
):

    print()

    print("=" * 70)
    print("VERIFY SPLIT")
    print("=" * 70)

    print()

    print("Train Last Sample")

    print(X_train[-1][-1][:5])

    print()

    print("Validation First Sample")

    print(X_validation[0][0][:5])

    print()

    print("Test First Sample")

    print(X_test[0][0][:5])