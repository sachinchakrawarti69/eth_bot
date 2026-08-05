import unittest
import numpy as np
from models.shared.core import ModelConfig, SequencePreprocessor, classification_diagnostics, regression_metrics
class SharedCoreTests(unittest.TestCase):
    def test_sequence_preprocessing(self):
        values=np.arange(30,dtype=np.float32).reshape(10,3); processor=SequencePreprocessor(); x,y=processor.create_sequences(processor.fit_transform(values),3)
        self.assertEqual(x.shape,(7,3,3)); self.assertEqual(y.shape,(7,))
    def test_metrics(self): self.assertEqual(regression_metrics([1,2],[1,2])["mse"],0.0)
    def test_classification_diagnostics(self): self.assertEqual(classification_diagnostics([0,1],[0.1,0.9])["confusion_matrix"].shape,(2,2))
    def test_config_validation(self):
        with self.assertRaises(ValueError): ModelConfig(sequence_length=0)
if __name__ == "__main__": unittest.main()
