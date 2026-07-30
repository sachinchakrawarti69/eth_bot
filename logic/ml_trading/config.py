"""
Configuration file for ML Trading Bot
"""
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'ETH.db'
MODEL_DIR = Path(__file__).parent / 'models'
LOG_DIR = BASE_DIR / 'logs'

MODEL_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

BINANCE_API_KEY = "YOUR_API_KEY_HERE"
BINANCE_SECRET_KEY = "YOUR_SECRET_KEY_HERE"

USE_TESTNET = True
BINANCE_TESTNET_URL = "https://testnet.binance.vision"

SYMBOL = "ETHUSDT"
QUANTITY = 0.001
ORDER_TYPE = "MARKET"

STOP_LOSS_PERCENT = 0.02
TAKE_PROFIT_PERCENT = 0.04
MAX_POSITION_SIZE = 0.01
MAX_DAILY_TRADES = 5
MIN_CONFIDENCE = 0.60

TRAIN_SPLIT = 0.8
LOOKBACK_DAYS = 30
PREDICTION_DAYS = 1

FEATURES = [
    'open', 'high', 'low', 'close', 'volume',
    'SMA_7', 'SMA_20', 'SMA_50',
    'RSI_14', 'MACD', 'MACD_signal',
    'BB_upper', 'BB_middle', 'BB_lower',
    'ATR_14'
]

LOG_FILE = LOG_DIR / 'trading.log'
