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
print("TEST EARLY STOPPING")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

from llm.lstm.training.early_stopping import (
    EarlyStoppingFactory,
)

# ----------------------------------------------------------
# Default
# ----------------------------------------------------------

print()
print("Creating Default EarlyStopping...")

callback = EarlyStoppingFactory.get()

print(type(callback).__name__)

assert type(callback).__name__ == "EarlyStopping"

print("Passed")

# ----------------------------------------------------------
# Custom
# ----------------------------------------------------------

print()
print("Creating Custom EarlyStopping...")

callback = EarlyStoppingFactory.get(
    monitor="loss",
    patience=5,
    restore_best_weights=False,
)

print(type(callback).__name__)

assert callback.monitor == "loss"
assert callback.patience == 5
assert callback.restore_best_weights is False

print("Passed")

print()
print("=" * 70)
print("EARLY STOPPING TEST PASSED")
print("=" * 70)