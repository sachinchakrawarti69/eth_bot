import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.datasets.dataloader import LSTMDataLoader


print("=" * 70)
print("TEST DATALOADER")
print("=" * 70)

loader = LSTMDataLoader(

    batch_size=32,

    sequence_length=60,

)

loader.summary()

print()

# ==========================================================
# Train
# ==========================================================

print("=" * 70)
print("TRAIN BATCHES")
print("=" * 70)

count = 0

for X_batch, y_batch in loader.train_loader():

    count += 1

    print()

    print("Batch :", count)

    print("X :", X_batch.shape)

    print("y :", y_batch.shape)

    if count == 3:
        break

print()

# ==========================================================
# Validation
# ==========================================================

print("=" * 70)
print("VALIDATION")
print("=" * 70)

for X_batch, y_batch in loader.validation_loader():

    print("X :", X_batch.shape)

    print("y :", y_batch.shape)

    break

print()

# ==========================================================
# Test
# ==========================================================

print("=" * 70)
print("TEST")
print("=" * 70)

for X_batch, y_batch in loader.test_loader():

    print("X :", X_batch.shape)

    print("y :", y_batch.shape)

    break

print()

print("=" * 70)
print("FIRST SAMPLE")
print("=" * 70)

print(X_batch[0])

print()

print("=" * 70)
print("FIRST LABEL")
print("=" * 70)

print(y_batch[0])

print()

print("=" * 70)
print("DATALOADER TEST PASSED")
print("=" * 70)