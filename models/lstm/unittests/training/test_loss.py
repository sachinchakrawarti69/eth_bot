import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(
    0,
    str(ROOT),
)

print("=" * 70)
print("TEST LOSS")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

from models.lstm.training.loss import (
    LossFactory,
)

# ----------------------------------------------------------
# MSE
# ----------------------------------------------------------

print()
print("Testing MSE")

loss = LossFactory.get("mse")

print(type(loss).__name__)

assert type(loss).__name__ == "MeanSquaredError"

print("Passed")

# ----------------------------------------------------------
# MAE
# ----------------------------------------------------------

print()
print("Testing MAE")

loss = LossFactory.get("mae")

print(type(loss).__name__)

assert type(loss).__name__ == "MeanAbsoluteError"

print("Passed")

# ----------------------------------------------------------
# Binary Crossentropy
# ----------------------------------------------------------

print()
print("Testing Binary Crossentropy")

loss = LossFactory.get(
    "binary_crossentropy"
)

print(type(loss).__name__)

assert type(loss).__name__ == "BinaryCrossentropy"

print("Passed")

# ----------------------------------------------------------
# Categorical Crossentropy
# ----------------------------------------------------------

print()
print("Testing Categorical Crossentropy")

loss = LossFactory.get(
    "categorical_crossentropy"
)

print(type(loss).__name__)

assert type(loss).__name__ == "CategoricalCrossentropy"

print("Passed")

# ----------------------------------------------------------
# Huber
# ----------------------------------------------------------

print()
print("Testing Huber")

loss = LossFactory.get("huber")

print(type(loss).__name__)

assert type(loss).__name__ == "Huber"

print("Passed")

# ----------------------------------------------------------
# Invalid
# ----------------------------------------------------------

print()
print("Testing Invalid Loss")

try:

    LossFactory.get("abc")

except ValueError as e:

    print(e)

    print("Passed")

print()
print("=" * 70)
print("LOSS TEST PASSED")
print("=" * 70)