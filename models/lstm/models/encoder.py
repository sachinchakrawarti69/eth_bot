import tensorflow as tf

from tensorflow.keras.layers import (
    Input,
    LSTM,
    BatchNormalization,
    Dropout,
)

from tensorflow.keras.models import Model


# ==========================================================
# Build Encoder
# ==========================================================

def build_encoder(
    input_shape,
    latent_dim=128,
):

    inputs = Input(
        shape=input_shape,
        name="encoder_input",
    )

    x = LSTM(
        128,
        return_sequences=True,
    )(inputs)

    x = BatchNormalization()(x)

    x = Dropout(0.20)(x)

    encoded = LSTM(
        latent_dim,
        return_sequences=False,
        name="latent_vector",
    )(x)

    model = Model(
        inputs,
        encoded,
        name="LSTM_Encoder",
    )

    return model


# ==========================================================
# Summary
# ==========================================================

def print_model_summary(model):

    print("=" * 70)
    print("ENCODER")
    print("=" * 70)

    model.summary()


# ==========================================================
# Save
# ==========================================================

def save_model(
    model,
    filepath,
):

    model.save(filepath)

    print("\nSaved:", filepath)


# ==========================================================
# Load
# ==========================================================

def load_model(filepath):

    return tf.keras.models.load_model(filepath)