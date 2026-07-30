import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.datasets.dataset import LSTMDataset


print("=" * 70)
print("TEST DATASET")
print("=" * 70)

dataset = LSTMDataset(

    sequence_length=60,

    target_column="close",

    normalize_method="standard",

)

dataset.load()

dataset.summary()

print()

print("=" * 70)
print("TRAIN")
print("=" * 70)

X_train, y_train = dataset.train()

print(X_train.shape)

print(y_train.shape)

print()

print("=" * 70)
print("VALIDATION")
print("=" * 70)

X_validation, y_validation = dataset.validation()

print(X_validation.shape)

print(y_validation.shape)

print()

print("=" * 70)
print("TEST")
print("=" * 70)

X_test, y_test = dataset.test()

print(X_test.shape)

print(y_test.shape)

print()

print("=" * 70)
print("FEATURES")
print("=" * 70)

print(dataset.feature_count())

print()

print(dataset.feature_names())

print()

print("=" * 70)
print("INPUT SHAPE")
print("=" * 70)

print(dataset.input_shape())

print()

print("=" * 70)
print("FIRST TRAIN SAMPLE")
print("=" * 70)

print(X_train[0])

print()

print("=" * 70)
print("FIRST LABEL")
print("=" * 70)

print(y_train[0])

print()

print("=" * 70)
print("DATASET TEST PASSED")
print("=" * 70)