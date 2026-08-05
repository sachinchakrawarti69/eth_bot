import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST REGRESSION METRICS")
print("=" * 70)

from models.lstm.evaluation.regression_metrics import (
    RegressionMetrics,
)

# ----------------------------------------------------------
# Sample Data
# ----------------------------------------------------------

y_true = [10, 20, 30, 40, 50]
y_pred = [12, 18, 33, 39, 48]

# ----------------------------------------------------------
# MAE
# ----------------------------------------------------------

print()
print("MAE")

mae = RegressionMetrics.mae(
    y_true,
    y_pred,
)

print(mae)

assert mae >= 0

print("Passed")

# ----------------------------------------------------------
# MSE
# ----------------------------------------------------------

print()
print("MSE")

mse = RegressionMetrics.mse(
    y_true,
    y_pred,
)

print(mse)

assert mse >= 0

print("Passed")

# ----------------------------------------------------------
# RMSE
# ----------------------------------------------------------

print()
print("RMSE")

rmse = RegressionMetrics.rmse(
    y_true,
    y_pred,
)

print(rmse)

assert rmse >= 0

print("Passed")

# ----------------------------------------------------------
# R2
# ----------------------------------------------------------

print()
print("R2 Score")

r2 = RegressionMetrics.r2(
    y_true,
    y_pred,
)

print(r2)

assert r2 <= 1

print("Passed")

# ----------------------------------------------------------
# Evaluate
# ----------------------------------------------------------

print()
print("Evaluate")

results = RegressionMetrics.evaluate(
    y_true,
    y_pred,
)

for key, value in results.items():
    print(f"{key:5} : {value}")

assert isinstance(results, dict)

print("Passed")

print()
print("=" * 70)
print("REGRESSION METRICS TEST PASSED")
print("=" * 70)