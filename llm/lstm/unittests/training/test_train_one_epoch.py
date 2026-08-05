import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST TRAIN ONE EPOCH")
print("=" * 70)

from llm.lstm.datasets.dataset import LSTMDataset
from llm.lstm.models.lstm_model import build_lstm_model
from llm.lstm.training.train_one_epoch import train_one_epoch

print()
print("Loading Dataset...")

dataset = LSTMDataset(sequence_length=60)
dataset.load()

X_train, y_train = dataset.train()
X_validation, y_validation = dataset.validation()

print("Done")

print()
print("Building Model...")

model = build_lstm_model(
    input_shape=dataset.input_shape(),
)

print("Done")

print()
print("=" * 70)
print("TRAINING ONE EPOCH")
print("=" * 70)

history = train_one_epoch(
    model,
    X_train,
    y_train,
    X_validation,
    y_validation,
    batch_size=32,
)

print()

print("Loss")
print(history.history["loss"][-1])

print()

print("Validation Loss")
print(history.history["val_loss"][-1])

print()

print("=" * 70)
print("TRAIN ONE EPOCH TEST PASSED")
print("=" * 70)