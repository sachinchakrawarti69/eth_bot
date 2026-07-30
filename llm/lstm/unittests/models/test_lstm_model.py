import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT))

from llm.lstm.datasets.dataset import LSTMDataset
from llm.lstm.models.lstm_model import (
    build_lstm_model,
    print_model_summary,
)

print("=" * 70)
print("TEST LSTM MODEL")
print("=" * 70)

# ----------------------------------------------------------
# Load Dataset
# ----------------------------------------------------------

dataset = LSTMDataset(

    sequence_length=60,

)

dataset.load()

print()

print("=" * 70)
print("DATASET")
print("=" * 70)

print(dataset.input_shape())

print()

# ----------------------------------------------------------
# Build Model
# ----------------------------------------------------------

model = build_lstm_model(

    input_shape=dataset.input_shape(),

)

print()

print_model_summary(model)

print()

print("=" * 70)
print("MODEL INFORMATION")
print("=" * 70)

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

print("=" * 70)
print("TEST PASSED")
print("=" * 70)