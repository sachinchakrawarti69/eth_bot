import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(
    0,
    str(ROOT),
)

print("=" * 70)
print("TEST METRICS")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

from llm.lstm.evaluation.metrics import (
    Metrics,
)

# ----------------------------------------------------------
# Sample Data
# ----------------------------------------------------------

y_true = [
    10,
    20,
    30,
    40,
    50,
]

y_pred = [
    12,
    18,
    33,
    39,
    48,
]

# ----------------------------------------------------------
# MAE
# ----------------------------------------------------------

print()
print("MAE")

mae = Metrics.mae(
    y_true,
    y_pred,
)

print(mae)

assert mae > 0

print("Passed")

# ----------------------------------------------------------
# MSE
# ----------------------------------------------------------

print()
print("MSE")

mse = Metrics.mse(
    y_true,
    y_pred,
)

print(mse)

assert mse > 0

print("Passed")

# ----------------------------------------------------------
# RMSE
# ----------------------------------------------------------

print()
print("RMSE")

rmse = Metrics.rmse(
    y_true,
    y_pred,
)

print(rmse)

assert rmse > 0

print("Passed")

# ----------------------------------------------------------
# R²
# ----------------------------------------------------------

print()
print("R2")

r2 = Metrics.r2(
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

results = Metrics.evaluate(
    y_true,
    y_pred,
)

for key, value in results.items():

    print(f"{key:5}: {value}")

assert "mae" in results
assert "mse" in results
assert "rmse" in results
assert "r2" in results

print("Passed")

print()
print("=" * 70)
print("METRICS TEST PASSED")
print("=" * 70)