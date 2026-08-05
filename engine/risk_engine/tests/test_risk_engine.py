"""
Unit tests for Risk Engine.
"""

import unittest

from risk_engine import RiskEngine


class TestRiskEngine(unittest.TestCase):

    def setUp(self):
        self.engine = RiskEngine()

    def test_engine_created(self):
        self.assertTrue(self.engine.initialized)

    def test_valid_trade(self):

        trade = {
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 3500,
            "confidence": 0.80,
        }

        self.assertTrue(self.engine.validate(trade))

    def test_invalid_trade(self):

        trade = {
            "symbol": "ETHUSDT",
            "side": "LONG",
        }

        self.assertFalse(self.engine.validate(trade))

    def test_trade_approved(self):

        trade = {
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 3500,
            "confidence": 0.80,
        }

        result = self.engine.approve(trade)

        self.assertTrue(result["approved"])

    def test_trade_rejected(self):

        trade = {
            "symbol": "ETHUSDT",
        }

        result = self.engine.approve(trade)

        self.assertFalse(result["approved"])


if __name__ == "__main__":
    unittest.main()