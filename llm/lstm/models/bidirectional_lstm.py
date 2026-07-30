import tensorflow as tf

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    LSTM,
    Dense,
    Dropout,
    BatchNormalization,
    Bidirectional,
)
from tensorflow.keras.optimizers import Adam


# ==========================================================
# Build Bidirectional LSTM
# ==========================================================

def build_bidirectional_lstm(
    input_shape,
    learning_rate=0.001,
):

    model = Sequential(

        [

            Bidirectional(

                LSTM(
                    128,
                    return_sequences=True,
                ),

                input_shape=input_shape,

            ),

            BatchNormalization(),

            Dropout(0.20),

            Bidirectional(

                LSTM(
                    64,
                    return_sequences=False,
                )

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
    print("BIDIRECTIONAL LSTM")
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

    print(f"\nModel Saved : {filepath}")


# ==========================================================
# Load
# ==========================================================

def load_model(filepath):

    return tf.keras.models.load_model(filepath)