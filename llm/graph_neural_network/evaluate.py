"""Evaluate GNN graph predictions."""
import argparse

import numpy as np
import tensorflow as tf
from llm.graph_neural_network.models import GraphAttention, GraphConvolution
from llm.shared import regression_metrics


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("model"); p.add_argument("nodes"); p.add_argument("edges"); p.add_argument("targets"); a=p.parse_args()
    model = tf.keras.models.load_model(a.model, custom_objects={"GraphConvolution": GraphConvolution, "GraphAttention": GraphAttention})
    print(regression_metrics(np.load(a.targets),model.predict([np.load(a.nodes),np.load(a.edges)],verbose=0)))
if __name__ == "__main__": main()
