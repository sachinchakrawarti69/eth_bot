import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf


class OptimizerFactory:
    """
    Creates TensorFlow optimizers.
    """

    @staticmethod
    def adam(
        learning_rate=0.001,
    ):
        return tf.keras.optimizers.Adam(
            learning_rate=learning_rate,
        )

    @staticmethod
    def sgd(
        learning_rate=0.01,
        momentum=0.9,
    ):
        return tf.keras.optimizers.SGD(
            learning_rate=learning_rate,
            momentum=momentum,
        )

    @staticmethod
    def rmsprop(
        learning_rate=0.001,
    ):
        return tf.keras.optimizers.RMSprop(
            learning_rate=learning_rate,
        )

    @staticmethod
    def get(
        name="adam",
        learning_rate=0.001,
    ):

        name = name.lower()

        if name == "adam":
            return OptimizerFactory.adam(
                learning_rate,
            )

        if name == "sgd":
            return OptimizerFactory.sgd(
                learning_rate,
            )

        if name == "rmsprop":
            return OptimizerFactory.rmsprop(
                learning_rate,
            )

        raise ValueError(
            f"Unknown optimizer: {name}"
        )