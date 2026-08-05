import unittest
import tensorflow as tf
from llm.transformer.config import CONFIG
from llm.transformer.models import build_transformer
class TransformerTests(unittest.TestCase):
    def test_shape(self): self.assertEqual(tuple(build_transformer(CONFIG)(tf.zeros((2,60,11))).shape),(2,1))
if __name__ == "__main__": unittest.main()
