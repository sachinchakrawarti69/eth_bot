from pathlib import Path

# ==========================================================
# ROOT PATHS
# ==========================================================

ROOT = Path(__file__).resolve().parents[2]

DATABASE_DIR = ROOT / "storage" / "database"
MODEL_DIR = ROOT / "storage" / "models"
REPORT_DIR = ROOT / "storage" / "reports"
LOG_DIR = ROOT / "storage" / "logs"

DATASET_DIR = ROOT / "llm" / "lstm" / "datasets"
CONFIG_DIR = ROOT / "llm" / "lstm" / "configs"

# ==========================================================
# DATABASE
# ==========================================================

DATABASE_PATH = DATABASE_DIR / "ETH.db"

# ==========================================================
# DATASET
# ==========================================================

SEQUENCE_LENGTH = 60

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

RANDOM_SEED = 42

# ==========================================================
# MODEL
# ==========================================================

INPUT_FEATURES = 11

LSTM_UNITS_1 = 128
LSTM_UNITS_2 = 64

DENSE_UNITS_1 = 32
DENSE_UNITS_2 = 16

DROPOUT = 0.20

OUTPUT_UNITS = 1

# ==========================================================
# TRAINING
# ==========================================================

EPOCHS = 50

BATCH_SIZE = 32

LEARNING_RATE = 0.001

LOSS = "mse"

METRICS = [
    "mae",
]

# ==========================================================
# EARLY STOPPING
# ==========================================================

EARLY_STOPPING_PATIENCE = 10

REDUCE_LR_PATIENCE = 5

REDUCE_LR_FACTOR = 0.5

# ==========================================================
# FILES
# ==========================================================

BEST_MODEL = MODEL_DIR / "best_model.keras"

FINAL_MODEL = MODEL_DIR / "final_model.keras"

CHECKPOINT = MODEL_DIR / "checkpoint.keras"

# ==========================================================
# REPORTS
# ==========================================================

CONFUSION_MATRIX = REPORT_DIR / "confusion_matrix.png"

ROC_CURVE = REPORT_DIR / "roc_curve.png"

LOSS_CURVE = REPORT_DIR / "loss_curve.png"

METRICS_REPORT = REPORT_DIR / "metrics.json"

# ==========================================================
# CREATE DIRECTORIES
# ==========================================================

for directory in [
    DATABASE_DIR,
    MODEL_DIR,
    REPORT_DIR,
    LOG_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )