import unittest
import tensorflow as tf
from llm.temporal_fusion_transformer.config import CONFIG
from llm.temporal_fusion_transformer.models import build_tft
class TFTTests(unittest.TestCase):
    def test_quantile_shape(self): self.assertEqual(tuple(build_tft(CONFIG)(tf.zeros((2,60,11))).shape),(2,3))
if __name__ == "__main__": unittest.main()
