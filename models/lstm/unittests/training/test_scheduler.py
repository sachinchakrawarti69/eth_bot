import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST SCHEDULER")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

from models.lstm.training.scheduler import (
    SchedulerFactory,
)

# ----------------------------------------------------------
# Default Scheduler
# ----------------------------------------------------------

print()
print("Creating Scheduler...")

scheduler = SchedulerFactory.get()

print(type(scheduler).__name__)

assert type(scheduler).__name__ == "ReduceLROnPlateau"

print("Passed")

# ----------------------------------------------------------
# Custom Scheduler
# ----------------------------------------------------------

print()
print("Creating Custom Scheduler...")

scheduler = SchedulerFactory.get(
    monitor="loss",
    factor=0.2,
    patience=2,
)

print(type(scheduler).__name__)

assert scheduler.monitor == "loss"

print("Passed")

# ----------------------------------------------------------
# Invalid Scheduler
# ----------------------------------------------------------

print()
print("Testing Invalid Scheduler...")

try:

    SchedulerFactory.get(
        "abc",
    )

except ValueError as e:

    print(e)

    print("Passed")

print()
print("=" * 70)
print("SCHEDULER TEST PASSED")
print("=" * 70)