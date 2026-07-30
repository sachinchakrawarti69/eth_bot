import os
import sys

from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST ENCODER")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

print("Importing Dataset...")

from llm.lstm.datasets.dataset import LSTMDataset

print("OK")

print()

print("Importing Encoder...")

from llm.lstm.models.encoder import (

    build_encoder,

    print_model_summary,

)

print("OK")

# ----------------------------------------------------------
# Dataset
# ----------------------------------------------------------

dataset = LSTMDataset(

    sequence_length=60,

)

print()

print("Loading Dataset...")

dataset.load()

print("OK")

X_train, y_train = dataset.train()

print()

print("Train Shape")

print(X_train.shape)

print()

print("Label Shape")

print(y_train.shape)

print()

print("Input Shape")

print(dataset.input_shape())

# ----------------------------------------------------------
# Build Model
# ----------------------------------------------------------

print()

print("Building Encoder...")

model = build_encoder(

    input_shape=dataset.input_shape(),

    latent_dim=128,

)

print("OK")

print()

print_model_summary(model)

print()

print("=" * 70)
print("MODEL INFORMATION")
print("=" * 70)

print()

print("Input")

print(model.input_shape)

print()

print("Output")

print(model.output_shape)

print()

print("Parameters")

print(model.count_params())

print()

print("=" * 70)
print("FORWARD PASS")
print("=" * 70)

latent = model.predict(

    X_train[:5],

    verbose=0,

)

print()

print("Latent Shape")

print(latent.shape)

print()

print(latent)

print()

print("=" * 70)
print("TEST PASSED")
print("=" * 70)