import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST TRAINER")
print("=" * 70)

# ----------------------------------------------------------
# Imports
# ----------------------------------------------------------

from llm.lstm.datasets.dataset import LSTMDataset

from llm.lstm.models.lstm_model import (

    build_lstm_model,

)

from llm.lstm.training.trainer import (

    Trainer,

)

# ----------------------------------------------------------
# Dataset
# ----------------------------------------------------------

print()

print("Loading Dataset...")

dataset = LSTMDataset(

    sequence_length=60,

)

dataset.load()

print("Done")

X_train, y_train = dataset.train()

X_validation, y_validation = dataset.validation()

X_test, y_test = dataset.test()

print()

print("Train")

print(X_train.shape)

print(y_train.shape)

print()

print("Validation")

print(X_validation.shape)

print(y_validation.shape)

print()

print("Test")

print(X_test.shape)

print(y_test.shape)

# ----------------------------------------------------------
# Model
# ----------------------------------------------------------

print()

print("Building Model...")

model = build_lstm_model(

    input_shape=dataset.input_shape(),

)

print("Done")

# ----------------------------------------------------------
# Trainer
# ----------------------------------------------------------

trainer = Trainer(

    model,

)

trainer.summary()

# ----------------------------------------------------------
# Train
# ----------------------------------------------------------

print()

print("=" * 70)
print("TRAINING")
print("=" * 70)

history = trainer.train(

    X_train,

    y_train,

    X_validation,

    y_validation,

    epochs=2,

    batch_size=32,

)

print()

print("Training Finished")

# ----------------------------------------------------------
# Evaluate
# ----------------------------------------------------------

print()

print("=" * 70)
print("EVALUATION")
print("=" * 70)

loss, mae = trainer.evaluate(

    X_test,

    y_test,

)

print()

print("Loss :", loss)

print("MAE  :", mae)

# ----------------------------------------------------------
# Prediction
# ----------------------------------------------------------

print()

print("=" * 70)
print("PREDICTION")
print("=" * 70)

prediction = trainer.predict(

    X_test[:5],

)

print(prediction)

# ----------------------------------------------------------
# Save
# ----------------------------------------------------------

print()

print("=" * 70)
print("SAVE MODEL")
print("=" * 70)

trainer.save()

print()

print("=" * 70)
print("TRAINER TEST PASSED")
print("=" * 70)