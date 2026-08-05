import unittest
import tensorflow as tf
from llm.graph_neural_network.config import CONFIG
from llm.graph_neural_network.models import build_gnn
from llm.graph_neural_network.datasets.graph_dataset import correlation_adjacency
class GNNTests(unittest.TestCase):
    def test_graph_shape(self): self.assertEqual(tuple(build_gnn(CONFIG,3)([tf.zeros((2,3,11)),tf.ones((2,3,3))]).shape),(2,1))
    def test_adjacency(self): self.assertEqual(correlation_adjacency([[1,2],[2,3],[3,4]]).shape,(2,2))
if __name__ == "__main__": unittest.main()
