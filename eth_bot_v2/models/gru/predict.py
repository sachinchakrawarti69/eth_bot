"""Run batch or single-candle GRU predictions."""
from __future__ import annotations
import argparse
import numpy as np
import tensorflow as tf
from models.shared.core import predict_batch
def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("model"); parser.add_argument("samples"); args = parser.parse_args()
    print(predict_batch(tf.keras.models.load_model(args.model), np.load(args.samples)))
if __name__ == "__main__": main()
