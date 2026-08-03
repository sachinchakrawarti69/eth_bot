import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST CLASSIFICATION METRICS")
print("=" * 70)

from llm.lstm.evaluation.classification_metrics import (
    ClassificationMetrics,
)

y_true = [1, 0, 1, 1, 0, 1]
y_pred = [1, 0, 1, 0, 0, 1]

# --------------------------------------------------
print()
print("Accuracy")

accuracy = ClassificationMetrics.accuracy(
    y_true,
    y_pred,
)

print(accuracy)

assert 0 <= accuracy <= 1

print("Passed")

# --------------------------------------------------
print()
print("Precision")

precision = ClassificationMetrics.precision(
    y_true,
    y_pred,
)

print(precision)

assert 0 <= precision <= 1

print("Passed")

# --------------------------------------------------
print()
print("Recall")

recall = ClassificationMetrics.recall(
    y_true,
    y_pred,
)

print(recall)

assert 0 <= recall <= 1

print("Passed")

# --------------------------------------------------
print()
print("F1 Score")

f1 = ClassificationMetrics.f1(
    y_true,
    y_pred,
)

print(f1)

assert 0 <= f1 <= 1

print("Passed")

# --------------------------------------------------
print()
print("Classification Report")

report = ClassificationMetrics.report(
    y_true,
    y_pred,
)

print(report)

assert isinstance(report, str)

print("Passed")

print()
print("=" * 70)
print("CLASSIFICATION METRICS TEST PASSED")
print("=" * 70)