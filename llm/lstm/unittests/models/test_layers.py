import os
import sys

from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT))

from tensorflow.keras.layers import Input
from tensorflow.keras.models import Sequential
from tensorflow.keras import Model

from llm.lstm.models.layers import *

print("=" * 70)
print("TEST LAYERS")
print("=" * 70)

# ==========================================================
# LSTM BLOCK
# ==========================================================

print("\nTesting LSTM Block")

model = Sequential(name="LSTM_Block")

model.add(Input(shape=(60, 20)))

for layer in lstm_block(

    64,

    return_sequences=False,

):

    model.add(layer)

model.summary()

print("Parameters:", count_parameters(model))

# ==========================================================
# Bidirectional
# ==========================================================

print("\nTesting Bidirectional")

model = Sequential(name="Bidirectional")

model.add(Input(shape=(60, 20)))

for layer in bidirectional_lstm_block(

    64,

    return_sequences=False,

):

    model.add(layer)

model.summary()

# ==========================================================
# GRU
# ==========================================================

print("\nTesting GRU")

model = Sequential(name="GRU")

model.add(Input(shape=(60, 20)))

for layer in gru_block(

    64,

    return_sequences=False,

):

    model.add(layer)

model.summary()

# ==========================================================
# CNN
# ==========================================================

print("\nTesting CNN")

model = Sequential(name="CNN")

model.add(Input(shape=(60, 20)))

for layer in cnn_block():

    model.add(layer)

model.summary()

# ==========================================================
# Dense
# ==========================================================

print("\nTesting Dense")

model = Sequential(name="Dense")

model.add(Input(shape=(64,)))

for layer in dense_block(32):

    model.add(layer)

model.add(output_layer())

model.summary()

# ==========================================================
# Attention
# ==========================================================

print("\nTesting Attention")

inputs = Input(shape=(60, 32))

attention = attention_layer()([inputs, inputs])

model = Model(

    inputs,

    attention,

    name="Attention",

)

model.summary()

print()

print("=" * 70)
print("ALL LAYERS TEST PASSED")
print("=" * 70)