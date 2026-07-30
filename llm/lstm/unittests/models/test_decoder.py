import os
import sys
import numpy as np

from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT))

print("=" * 70)
print("TEST DECODER")
print("=" * 70)

from llm.lstm.models.decoder import (

    build_decoder,

    print_model_summary,

)

print()

print("Building Decoder...")

model = build_decoder(

    latent_dim=128,

    output_steps=5,

)

print("OK")

print()

print_model_summary(model)

print()

print("=" * 70)
print("MODEL INFORMATION")
print("=" * 70)

print()

print("Input Shape")

print(model.input_shape)

print()

print("Output Shape")

print(model.output_shape)

print()

print("Parameters")

print(model.count_params())

print()

print("Loss")

print(model.loss)

print()

print("Optimizer")

print(type(model.optimizer).__name__)

print()

print("=" * 70)
print("FORWARD PASS")
print("=" * 70)

latent = np.random.rand(

    3,

    128,

).astype(np.float32)

prediction = model.predict(

    latent,

    verbose=0,

)

print()

print("Input")

print(latent.shape)

print()

print("Prediction")

print(prediction.shape)

print()

print(prediction)

print()

print("=" * 70)
print("TEST PASSED")
print("=" * 70)