import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST ROC CURVE")
print("=" * 70)

from llm.lstm.evaluation.roc_curve import ROCCurve

# -------------------------------------------------------
# Dummy Binary Labels
# -------------------------------------------------------

y_true = [
    0,
    0,
    1,
    1,
    0,
    1,
    0,
    1,
]

y_score = [
    0.10,
    0.30,
    0.60,
    0.80,
    0.20,
    0.75,
    0.40,
    0.90,
]

# -------------------------------------------------------
# Compute
# -------------------------------------------------------

print()
print("Computing ROC...")

(
    fpr,
    tpr,
    thresholds,
    roc_auc,
) = ROCCurve.compute(
    y_true,
    y_score,
)

print()

print("False Positive Rate")
print(fpr)

print()

print("True Positive Rate")
print(tpr)

print()

print("Thresholds")
print(thresholds)

print()

print("AUC")
print(roc_auc)

assert roc_auc > 0

print("Passed")

# -------------------------------------------------------
# Plot
# -------------------------------------------------------

print()
print("Generating Plot...")

ROCCurve.plot(
    y_true,
    y_score,
    save_path="storage/reports/roc_curve.png",
)

print("Passed")

print()
print("=" * 70)
print("ROC CURVE TEST PASSED")
print("=" * 70)