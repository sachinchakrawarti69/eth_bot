import os
import sys
from pathlib import Path

# ----------------------------------------------------------
# Reduce TensorFlow logging
# ----------------------------------------------------------

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST STACKED LSTM")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

print("\n[1] Importing Dataset...")

from llm.lstm.datasets.dataset import LSTMDataset

print("OK")

print("\n[2] Importing Model...")

from llm.lstm.models.stacked_lstm import (
    build_stacked_lstm,
    print_model_summary,
)

print("OK")

# ----------------------------------------------------------
# Dataset
# ----------------------------------------------------------

print("\n[3] Creating Dataset Object...")

dataset = LSTMDataset(
    sequence_length=60,
)

print("OK")

print("\n[4] Loading Dataset...")

dataset.load()

print("OK")

# ----------------------------------------------------------
# Shapes
# ----------------------------------------------------------

print("\nDataset Summary")

X_train, y_train = dataset.train()

X_validation, y_validation = dataset.validation()

X_test, y_test = dataset.test()

print("Train      :", X_train.shape, y_train.shape)
print("Validation :", X_validation.shape, y_validation.shape)
print("Test       :", X_test.shape, y_test.shape)

print()

print("Input Shape")

print(dataset.input_shape())

# ----------------------------------------------------------
# Model
# ----------------------------------------------------------

print("\n[5] Building Model...")

model = build_stacked_lstm(
    input_shape=dataset.input_shape(),
)

print("OK")

# ----------------------------------------------------------
# Summary
# ----------------------------------------------------------

print("\n[6] Printing Summary...")

print_model_summary(model)

print("OK")

# ----------------------------------------------------------
# Information
# ----------------------------------------------------------

print()

print("=" * 70)
print("MODEL INFO")
print("=" * 70)

print()

print("Input Shape")

print(model.input_shape)

print()

print("Output Shape")

print(model.output_shape)

print()

print("Loss")

print(model.loss)

print()

print("Optimizer")

print(type(model.optimizer).__name__)

print()

print("Parameters")

print(model.count_params())

# ----------------------------------------------------------
# Layers
# ----------------------------------------------------------

print()

print("=" * 70)
print("LAYERS")
print("=" * 70)

for i, layer in enumerate(model.layers):

    print(
        f"{i+1:02d}",
        layer.name,
        type(layer).__name__,
    )

# ----------------------------------------------------------
# Prediction
# ----------------------------------------------------------

print()

print("=" * 70)
print("FORWARD PASS")
print("=" * 70)

sample = X_train[:5]

print("Input Batch")

print(sample.shape)

print()

print("[7] Predicting...")

prediction = model.predict(
    sample,
    verbose=1,
)

print("Prediction Finished")

print()

print("Prediction Shape")

print(prediction.shape)

print()

print(prediction)

# ----------------------------------------------------------
# Completed
# ----------------------------------------------------------

print()

print("=" * 70)
print("TEST PASSED")
print("=" * 70)