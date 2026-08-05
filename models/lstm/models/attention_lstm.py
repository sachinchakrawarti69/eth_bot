import tensorflow as tf

from tensorflow.keras.layers import (
    Input,
    LSTM,
    Dense,
    Dropout,
    BatchNormalization,
    Attention,
    GlobalAveragePooling1D,
)

from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam


# ==========================================================
# Build Attention LSTM
# ==========================================================

def build_attention_lstm(
    input_shape,
    learning_rate=0.001,
):

    inputs = Input(shape=input_shape)

    # ------------------------------------------------------
    # LSTM Encoder
    # ------------------------------------------------------

    x = LSTM(
        128,
        return_sequences=True,
    )(inputs)

    x = BatchNormalization()(x)

    x = Dropout(0.20)(x)

    x = LSTM(
        64,
        return_sequences=True,
    )(x)

    x = BatchNormalization()(x)

    # ------------------------------------------------------
    # Self Attention
    # ------------------------------------------------------

    attention = Attention()([x, x])

    # ------------------------------------------------------
    # Pool
    # ------------------------------------------------------

    x = GlobalAveragePooling1D()(attention)

    # ------------------------------------------------------
    # Dense Layers
    # ------------------------------------------------------

    x = Dense(
        64,
        activation="relu",
    )(x)

    x = Dropout(0.20)(x)

    x = Dense(
        32,
        activation="relu",
    )(x)

    outputs = Dense(
        1,
        activation="linear",
    )(x)

    model = Model(
        inputs=inputs,
        outputs=outputs,
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
    print("ATTENTION LSTM")
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