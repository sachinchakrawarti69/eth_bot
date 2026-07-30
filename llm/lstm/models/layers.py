import tensorflow as tf

from tensorflow.keras.layers import (
    LSTM,
    GRU,
    Dense,
    Dropout,
    BatchNormalization,
    Bidirectional,
    Conv1D,
    MaxPooling1D,
    Attention,
)


# ==========================================================
# LSTM Block
# ==========================================================

def lstm_block(
    units,
    return_sequences=True,
    dropout=0.20,
):

    return [

        LSTM(
            units,
            return_sequences=return_sequences,
        ),

        BatchNormalization(),

        Dropout(dropout),

    ]


# ==========================================================
# Bidirectional LSTM Block
# ==========================================================

def bidirectional_lstm_block(
    units,
    return_sequences=True,
    dropout=0.20,
):

    return [

        Bidirectional(

            LSTM(
                units,
                return_sequences=return_sequences,
            )

        ),

        BatchNormalization(),

        Dropout(dropout),

    ]


# ==========================================================
# GRU Block
# ==========================================================

def gru_block(
    units,
    return_sequences=True,
    dropout=0.20,
):

    return [

        GRU(
            units,
            return_sequences=return_sequences,
        ),

        BatchNormalization(),

        Dropout(dropout),

    ]


# ==========================================================
# CNN Block
# ==========================================================

def cnn_block(
    filters=64,
    kernel_size=3,
):

    return [

        Conv1D(

            filters=filters,

            kernel_size=kernel_size,

            padding="same",

            activation="relu",

        ),

        BatchNormalization(),

        MaxPooling1D(2),

    ]


# ==========================================================
# Dense Block
# ==========================================================

def dense_block(
    units,
    dropout=0.20,
):

    return [

        Dense(
            units,
            activation="relu",
        ),

        Dropout(dropout),

    ]


# ==========================================================
# Attention Layer
# ==========================================================

def attention_layer():

    return Attention()


# ==========================================================
# Output Layer
# ==========================================================

def output_layer():

    return Dense(

        1,

        activation="linear",

        name="prediction",

    )


# ==========================================================
# Count Parameters
# ==========================================================

def count_parameters(model):

    return model.count_params()


# ==========================================================
# Print Summary
# ==========================================================

def print_summary(model):

    print("=" * 70)

    print(model.name)

    print("=" * 70)

    model.summary()