import tensorflow as tf

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    LSTM,
    Dense,
    Dropout,
    BatchNormalization,
)
from tensorflow.keras.optimizers import Adam


# ==========================================================
# Build Stacked LSTM
# ==========================================================

def build_stacked_lstm(
    input_shape,
    learning_rate=0.001,
):
    """
    3-Layer Stacked LSTM
    """

    model = Sequential(

        [

            LSTM(
                128,
                return_sequences=True,
                input_shape=input_shape,
            ),

            BatchNormalization(),

            Dropout(0.20),

            LSTM(
                64,
                return_sequences=True,
            ),

            BatchNormalization(),

            Dropout(0.20),

            LSTM(
                32,
                return_sequences=False,
            ),

            Dropout(0.20),

            Dense(
                64,
                activation="relu",
            ),

            Dense(
                32,
                activation="relu",
            ),

            Dense(
                1,
                activation="linear",
            ),

        ]

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
    print("STACKED LSTM")
    print("=" * 70)

    model.summary()


# ==========================================================
# Save
# ==========================================================

def save_model(
    model,
    path,
):

    model.save(path)

    print("\nSaved:", path)


# ==========================================================
# Load
# ==========================================================

def load_model(path):

    return tf.keras.models.load_model(path)