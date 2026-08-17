import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST OPTIMIZER")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

from models.lstm.training.optimizer import (
    OptimizerFactory,
)

# ----------------------------------------------------------
# Adam
# ----------------------------------------------------------

print()
print("Creating Adam Optimizer...")

optimizer = OptimizerFactory.get(
    "adam",
)

print(type(optimizer).__name__)

assert type(optimizer).__name__ == "Adam"

print("Passed")

# ----------------------------------------------------------
# SGD
# ----------------------------------------------------------

print()
print("Creating SGD Optimizer...")

optimizer = OptimizerFactory.get(
    "sgd",
)

print(type(optimizer).__name__)

assert type(optimizer).__name__ == "SGD"

print("Passed")

# ----------------------------------------------------------
# RMSprop
# ----------------------------------------------------------

print()
print("Creating RMSprop Optimizer...")

optimizer = OptimizerFactory.get(
    "rmsprop",
)

print(type(optimizer).__name__)

assert type(optimizer).__name__ == "RMSprop"

print("Passed")

# ----------------------------------------------------------
# Invalid
# ----------------------------------------------------------

print()
print("Testing Invalid Optimizer...")

try:

    OptimizerFactory.get("abc")

except ValueError as e:

    print(e)

    print("Passed")

print()

print("=" * 70)
print("OPTIMIZER TEST PASSED")
print("=" * 70)