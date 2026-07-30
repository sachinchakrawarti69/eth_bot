import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.pipeline import run_pipeline


print("=" * 70)
print("TEST COMPLETE PREPROCESSING PIPELINE")
print("=" * 70)

dataset = run_pipeline()

print()

print("=" * 70)
print("TRAIN")
print("=" * 70)

print(dataset["X_train"].shape)
print(dataset["y_train"].shape)

print()

print("=" * 70)
print("VALIDATION")
print("=" * 70)

print(dataset["X_validation"].shape)
print(dataset["y_validation"].shape)

print()

print("=" * 70)
print("TEST")
print("=" * 70)

print(dataset["X_test"].shape)
print(dataset["y_test"].shape)

print()

print("=" * 70)
print("FEATURE COUNT")
print("=" * 70)

print(len(dataset["features"]))

print()

print("=" * 70)
print("FEATURE NAMES")
print("=" * 70)

for feature in dataset["features"]:
    print(feature)

print()

print("=" * 70)
print("FIRST TRAIN SAMPLE")
print("=" * 70)

print(dataset["X_train"][0])

print()

print("=" * 70)
print("FIRST TARGET")
print("=" * 70)

print(dataset["y_train"][0])

print()

print("=" * 70)
print("PIPELINE TEST PASSED")
print("=" * 70)