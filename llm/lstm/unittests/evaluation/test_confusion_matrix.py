import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(
    0,
    str(ROOT),
)

print("=" * 70)
print("TEST CONFUSION MATRIX")
print("=" * 70)

from llm.lstm.evaluation.confusion_matrix import (
    ConfusionMatrix,
)

# ----------------------------------------------------------
# Sample Data
# ----------------------------------------------------------

y_true = [
    1,
    0,
    1,
    1,
    0,
    1,
    0,
    0,
    1,
    0,
]

y_pred = [
    1,
    0,
    1,
    0,
    0,
    1,
    1,
    0,
    1,
    0,
]

# ----------------------------------------------------------
# Compute
# ----------------------------------------------------------

print()
print("Computing Confusion Matrix...")

cm = ConfusionMatrix.compute(
    y_true,
    y_pred,
)

print(cm)

assert cm.shape == (2, 2)

print("Passed")

# ----------------------------------------------------------
# Print
# ----------------------------------------------------------

print()
print("Printing Matrix...")

ConfusionMatrix.print(
    y_true,
    y_pred,
)

print("Passed")

# ----------------------------------------------------------
# Display
# ----------------------------------------------------------

print()
print("Displaying Matrix...")

ConfusionMatrix.display(
    y_true,
    y_pred,
    labels=[
        "Negative",
        "Positive",
    ],
)

print("Passed")

print()
print("=" * 70)
print("CONFUSION MATRIX TEST PASSED")
print("=" * 70)