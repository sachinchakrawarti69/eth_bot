import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.datasets.dataset import LSTMDataset
from llm.lstm.datasets.sequence_dataset import SequenceDataset


print("=" * 70)
print("TEST SEQUENCE DATASET")
print("=" * 70)

dataset = LSTMDataset()

dataset.load()

X_train, y_train = dataset.train()

sequence_dataset = SequenceDataset(
    X_train,
    y_train,
)

sequence_dataset.summary()

print()

print("=" * 70)
print("DATASET LENGTH")
print("=" * 70)

print(len(sequence_dataset))

print()

print("=" * 70)
print("INPUT SHAPE")
print("=" * 70)

print(sequence_dataset.input_shape)

print()

print("=" * 70)
print("FEATURE COUNT")
print("=" * 70)

print(sequence_dataset.feature_count)

print()

print("=" * 70)
print("SEQUENCE LENGTH")
print("=" * 70)

print(sequence_dataset.sequence_length)

print()

print("=" * 70)
print("FIRST SAMPLE")
print("=" * 70)

X, y = sequence_dataset.first()

print("X Shape :", X.shape)
print("y :", y)

print()

print("=" * 70)
print("LAST SAMPLE")
print("=" * 70)

X, y = sequence_dataset.last()

print("X Shape :", X.shape)
print("y :", y)

print()

print("=" * 70)
print("INDEX TEST")
print("=" * 70)

X, y = sequence_dataset[10]

print("X Shape :", X.shape)
print("y :", y)

print()

print("=" * 70)
print("FIRST 5 TARGETS")
print("=" * 70)

for i in range(5):

    _, label = sequence_dataset[i]

    print(f"{i:2d} -> {label}")

print()

print("=" * 70)
print("SEQUENCE DATASET TEST PASSED")
print("=" * 70)