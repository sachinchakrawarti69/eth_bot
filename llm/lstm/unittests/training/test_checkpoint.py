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
print("TEST CHECKPOINT")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

from llm.lstm.training.checkpoint import (
    CheckpointFactory,
)

# ----------------------------------------------------------
# Default
# ----------------------------------------------------------

print()
print("Creating Default Checkpoint...")

checkpoint = CheckpointFactory.get()

print(type(checkpoint).__name__)

assert type(checkpoint).__name__ == "ModelCheckpoint"

print("Passed")

# ----------------------------------------------------------
# Custom
# ----------------------------------------------------------

print()
print("Creating Custom Checkpoint...")

checkpoint = CheckpointFactory.get(
    save_dir="storage/test_models",
    filename="model.keras",
    monitor="loss",
)

print(type(checkpoint).__name__)

assert checkpoint.monitor == "loss"

assert checkpoint.filepath.endswith(
    "model.keras"
)

print("Passed")

# ----------------------------------------------------------
# Verify Directory
# ----------------------------------------------------------

print()
print("Checking Directory...")

assert Path(
    "storage/test_models"
).exists()

print("Passed")

print()
print("=" * 70)
print("CHECKPOINT TEST PASSED")
print("=" * 70)