import unittest
import tensorflow as tf
from models.temporal_convolutional_network.config import CONFIG
from models.temporal_convolutional_network.models import build_tcn
class TCNTests(unittest.TestCase):
    def test_shape(self): self.assertEqual(tuple(build_tcn(CONFIG)(tf.zeros((2,60,11))).shape),(2,1))
if __name__ == "__main__": unittest.main()
