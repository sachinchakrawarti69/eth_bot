import os
import sys

from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST BIDIRECTIONAL LSTM")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

print("\nImporting Dataset...")

from llm.lstm.datasets.dataset import LSTMDataset

print("OK")

print("\nImporting Model...")

from llm.lstm.models.bidirectional_lstm import (

    build_bidirectional_lstm,

    print_model_summary,

)

print("OK")

# ----------------------------------------------------------
# Dataset
# ----------------------------------------------------------

dataset = LSTMDataset(

    sequence_length=60,

)

print("\nLoading Dataset...")

dataset.load()

print("OK")

print()

X_train, y_train = dataset.train()

print("Train :", X_train.shape)

print("Labels:", y_train.shape)

print()

print("Input Shape")

print(dataset.input_shape())

# ----------------------------------------------------------
# Build Model
# ----------------------------------------------------------

print()

print("Building Model...")

model = build_bidirectional_lstm(

    input_shape=dataset.input_shape(),

)

print("OK")

# ----------------------------------------------------------
# Summary
# ----------------------------------------------------------

print()

print_model_summary(model)

print()

print("=" * 70)
print("MODEL INFORMATION")
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
# Forward Pass
# ----------------------------------------------------------

print()

print("=" * 70)
print("FORWARD PASS")
print("=" * 70)

prediction = model.predict(

    X_train[:5],

    verbose=0,

)

print()

print("Prediction Shape")

print(prediction.shape)

print()

print(prediction)

print()

print("=" * 70)
print("TEST PASSED")
print("=" * 70)