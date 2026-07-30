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
# Build LSTM Model
# ==========================================================

def build_lstm_model(
    input_shape,
    learning_rate=0.001,
):
    """
    input_shape = (sequence_length, feature_count)
    """

    model = Sequential(

        [

            LSTM(
                128,
                return_sequences=True,
                input_shape=input_shape,
            ),

            Dropout(0.20),

            BatchNormalization(),

            LSTM(
                64,
                return_sequences=False,
            ),

            Dropout(0.20),

            Dense(
                32,
                activation="relu",
            ),

            Dense(
                16,
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
# Model Summary
# ==========================================================

def print_model_summary(model):

    print("=" * 70)
    print("LSTM MODEL")
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

    print(f"\nModel saved -> {filepath}")


# ==========================================================
# Load
# ==========================================================

def load_model(filepath):

    return tf.keras.models.load_model(filepath)