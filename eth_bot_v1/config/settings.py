"""
ETH Bot V1 - Configuration
Using OPEN/PUBLIC APIs - No keys required!
"""

from pathlib import Path

class Config:
    """Main configuration class"""
    
    # ============================================
    # PATHS
    # ============================================
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    MODELS_DIR = BASE_DIR / "models" / "saved_models"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Create directories
    for dir_path in [DATA_DIR, RAW_DATA_DIR, MODELS_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # ============================================
    # DATABASE
    # ============================================
    DB_PATH = DATA_DIR / "eth_bot.db"
    
    # ============================================
    # EXCHANGE SETTINGS - OPEN APIs (NO KEYS NEEDED)
    # ============================================
    SYMBOL = "ETH/USDT"
    TIMEFRAME = "1h"
    EXCHANGE = "binance"
    
    # ============================================
    # PUBLIC API ENDPOINTS (No keys needed)
    # ============================================
    BINANCE_PUBLIC_URL = "https://api.binance.com"
    COINGECKO_PUBLIC_URL = "https://api.coingecko.com/api/v3"
    DERIBIT_PUBLIC_URL = "https://www.deribit.com/api/v2"
    ETHERSCAN_PUBLIC_URL = "https://api.etherscan.io/api"
    
    # ============================================
    # TRADING SETTINGS
    # ============================================
    INITIAL_CAPITAL = 10000.0
    POSITION_SIZE = 0.1
    MAX_POSITIONS = 3
    STOP_LOSS = 0.05
    TAKE_PROFIT = 0.10
    
    # ============================================
    # MODEL SETTINGS
    # ============================================
    SEQUENCE_LENGTH = 24
    TRAIN_SPLIT = 0.8
    TEST_SPLIT = 0.1
    VALIDATION_SPLIT = 0.1
    
    LSTM_HIDDEN_SIZE = 64
    LSTM_NUM_LAYERS = 2
    LSTM_DROPOUT = 0.2
    
    EPOCHS = 50
    BATCH_SIZE = 32
    LEARNING_RATE = 0.001
    EARLY_STOPPING_PATIENCE = 10
    
    # ============================================
    # DATA COLLECTION
    # ============================================
    OHLCV_LIMIT = 500
    BACKFILL_DAYS = 30
    
    # ============================================
    # SCHEDULER
    # ============================================
    UPDATE_INTERVAL_MINUTES = 60
    MODEL_RETRAIN_HOURS = 24
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = LOGS_DIR / "eth_bot.log"
    
    # ============================================
    # FEATURES FLAGS
    # ============================================
    ENABLE_LIVE_TRADING = False
    ENABLE_PAPER_TRADING = True
    ENABLE_BACKTESTING = True
    ENABLE_MODEL_TRAINING = True
    ENABLE_DATA_COLLECTION = True
    
    @property
    def device(self):
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except:
            return "cpu"
    
    def __repr__(self):
        return f"""
        ========================================
        ETH BOT CONFIGURATION
        ========================================
        Symbol: {self.SYMBOL}
        Timeframe: {self.TIMEFRAME}
        Database: {self.DB_PATH}
        Initial Capital: ${self.INITIAL_CAPITAL:,.2f}
        Sequence Length: {self.SEQUENCE_LENGTH}
        Device: {self.device}
        Live Trading: {self.ENABLE_LIVE_TRADING}
        Paper Trading: {self.ENABLE_PAPER_TRADING}
        ========================================
        """

# Create config instance
config = Config()

# Print config if run directly
if __name__ == "__main__":
    print(config)