import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST VALIDATOR")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

from models.lstm.datasets.dataset import LSTMDataset

from models.lstm.models.lstm_model import (
    build_lstm_model,
)

from models.lstm.training.validate import (
    Validator,
)

# ----------------------------------------------------------
# Dataset
# ----------------------------------------------------------

print()
print("Loading Dataset...")

dataset = LSTMDataset(
    sequence_length=60,
)

dataset.load()

print("Done")

X_train, y_train = dataset.train()
X_validation, y_validation = dataset.validation()

# ----------------------------------------------------------
# Model
# ----------------------------------------------------------

print()
print("Building Model...")

model = build_lstm_model(
    input_shape=dataset.input_shape(),
)

print("Done")

# ----------------------------------------------------------
# Quick Training
# ----------------------------------------------------------

print()
print("Quick Training...")

model.fit(
    X_train,
    y_train,
    epochs=1,
    batch_size=32,
    verbose=1,
)

print("Done")

# ----------------------------------------------------------
# Validation
# ----------------------------------------------------------

validator = Validator(model)

print()
print("=" * 70)
print("VALIDATION")
print("=" * 70)

metrics = validator.validate(
    X_validation,
    y_validation,
)

print()

print("Loss :", metrics["loss"])
print("MAE  :", metrics["mae"])

print()
print("=" * 70)
print("VALIDATOR TEST PASSED")
print("=" * 70)