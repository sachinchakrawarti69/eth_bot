import tensorflow as tf

from tensorflow.keras.layers import (
    Input,
    RepeatVector,
    LSTM,
    Dense,
    Dropout,
    BatchNormalization,
)

from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam


# ==========================================================
# Build Decoder
# ==========================================================

def build_decoder(
    latent_dim=128,
    output_steps=1,
    learning_rate=0.001,
):

    inputs = Input(
        shape=(latent_dim,),
        name="decoder_input",
    )

    x = RepeatVector(output_steps)(inputs)

    x = LSTM(
        128,
        return_sequences=True,
    )(x)

    x = BatchNormalization()(x)

    x = Dropout(0.20)(x)

    x = LSTM(
        64,
        return_sequences=True,
    )(x)

    x = Dropout(0.20)(x)

    outputs = Dense(
        1,
        activation="linear",
        name="prediction",
    )(x)

    model = Model(
        inputs,
        outputs,
        name="LSTM_Decoder",
    )

    model.compile(

        optimizer=Adam(
            learning_rate=learning_rate,
        ),

        loss="mse",

        metrics=[
            "mae",
        ],

    )

    return model


# ==========================================================
# Summary
# ==========================================================

def print_model_summary(model):

    print("=" * 70)
    print("DECODER")
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