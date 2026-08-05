import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST PLOTS")
print("=" * 70)

from models.lstm.evaluation.plots import Plots


# ----------------------------------------------------------
# Dummy History
# ----------------------------------------------------------

class DummyHistory:

    history = {

        "loss": [
            0.80,
            0.60,
            0.40,
            0.30,
        ],

        "val_loss": [
            0.90,
            0.70,
            0.50,
            0.40,
        ],

        "mae": [
            0.60,
            0.45,
            0.30,
            0.20,
        ],

        "val_mae": [
            0.65,
            0.50,
            0.35,
            0.25,
        ],

    }


history = DummyHistory()

y_true = [
    10,
    20,
    30,
    40,
    50,
]

y_pred = [
    12,
    19,
    31,
    38,
    49,
]

OUTPUT = Path("storage/reports/plots")

OUTPUT.mkdir(
    parents=True,
    exist_ok=True,
)

# ----------------------------------------------------------
# Prediction Plot
# ----------------------------------------------------------

print()
print("Prediction Plot")

Plots.prediction_plot(

    y_true,

    y_pred,

    OUTPUT / "prediction.png",

)

assert (OUTPUT / "prediction.png").exists()

print("Passed")

# ----------------------------------------------------------
# Loss Curve
# ----------------------------------------------------------

print()
print("Loss Curve")

Plots.loss_curve(

    history,

    OUTPUT / "loss.png",

)

assert (OUTPUT / "loss.png").exists()

print("Passed")

# ----------------------------------------------------------
# MAE Curve
# ----------------------------------------------------------

print()
print("MAE Curve")

Plots.mae_curve(

    history,

    OUTPUT / "mae.png",

)

assert (OUTPUT / "mae.png").exists()

print("Passed")

# ----------------------------------------------------------
# Scatter Plot
# ----------------------------------------------------------

print()
print("Scatter Plot")

Plots.scatter_plot(

    y_true,

    y_pred,

    OUTPUT / "scatter.png",

)

assert (OUTPUT / "scatter.png").exists()

print("Passed")

print()

print("=" * 70)
print("PLOTS TEST PASSED")
print("=" * 70)