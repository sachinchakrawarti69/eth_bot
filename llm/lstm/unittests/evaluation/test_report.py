import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST REPORT")
print("=" * 70)

from llm.lstm.evaluation.report import EvaluationReport

# --------------------------------------------------------
# Dummy Metrics
# --------------------------------------------------------

metrics = {
    "loss": 0.15,
    "mae": 0.23,
    "mse": 0.08,
    "rmse": 0.28,
    "r2": 0.91,
}

# --------------------------------------------------------
# Save
# --------------------------------------------------------

report = EvaluationReport()

print()
print("Saving Report...")

path = report.save(metrics)

print("Passed")

# --------------------------------------------------------
# Load
# --------------------------------------------------------

print()
print("Loading Report...")

loaded = report.load()

print(loaded)

assert loaded == metrics

print("Passed")

# --------------------------------------------------------
# Print
# --------------------------------------------------------

print()
print("Printing Report...")

report.print(loaded)

print("Passed")

print()
print("=" * 70)
print("REPORT TEST PASSED")
print("=" * 70)