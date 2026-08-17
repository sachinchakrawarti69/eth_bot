import unittest
import tensorflow as tf
from models.gru.config import CONFIG
from models.gru.models import build_attention_gru, build_bidirectional_gru, build_gru, build_stacked_gru
class GRUModelTests(unittest.TestCase):
    def test_all_variants_produce_scalar_output(self):
        sample=tf.zeros((2, CONFIG.sequence_length, CONFIG.feature_count))
        for builder in (build_gru, build_stacked_gru, build_bidirectional_gru, build_attention_gru): self.assertEqual(tuple(builder(CONFIG)(sample).shape), (2, 1))
if __name__ == "__main__": unittest.main()
