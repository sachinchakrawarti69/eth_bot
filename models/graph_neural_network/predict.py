"""Predict from node and adjacency NumPy arrays."""
import argparse

import numpy as np
import tensorflow as tf

# Importing registers the custom layers used by the saved GNN model.
from models.graph_neural_network.models import GraphAttention, GraphConvolution


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("model")
    p.add_argument("nodes")
    p.add_argument("edges")
    a = p.parse_args()
    model = tf.keras.models.load_model(
        a.model,
        custom_objects={"GraphConvolution": GraphConvolution, "GraphAttention": GraphAttention},
    )
    print(model.predict([np.load(a.nodes), np.load(a.edges)], verbose=0))
if __name__ == "__main__": main()
