"""Evaluate a saved GRU model."""
from __future__ import annotations
import argparse
import numpy as np
import tensorflow as tf
from models.shared import regression_metrics
def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("model"); parser.add_argument("x_test"); parser.add_argument("y_test"); args = parser.parse_args()
    print(regression_metrics(np.load(args.y_test), tf.keras.models.load_model(args.model).predict(np.load(args.x_test), verbose=0)))
if __name__ == "__main__": main()
