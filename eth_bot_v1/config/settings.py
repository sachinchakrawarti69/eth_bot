"""
Configuration settings for ETH Bot Fast
Using OPEN/PUBLIC APIs - No API keys required!
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (optional)
load_dotenv()

class Config:
    """Main configuration class - All settings centralized"""
    
    # ============================================
    # PATHS
    # ============================================
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    MODELS_DIR = BASE_DIR / "models" / "saved_models"
    LOGS_DIR = BASE_DIR / "logs"
    NOTEBOOKS_DIR = BASE_DIR / "notebooks"
    
    # Create directories if they don't exist
    for dir_path in [DATA_DIR, RAW_DATA_DIR, MODELS_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # ============================================
    # DATABASE
    # ============================================
    DB_PATH = DATA_DIR / "eth_bot.db"
    DB_CONNECTION_TIMEOUT = 30  # seconds
    
    # ============================================
    # EXCHANGE SETTINGS - OPEN APIs (NO KEYS NEEDED)
    # ============================================
    SYMBOL = os.getenv("SYMBOL", "ETH/USDT")
    TIMEFRAME = os.getenv("TIMEFRAME", "1h")
    EXCHANGE = os.getenv("EXCHANGE", "binance")
    
    # Public endpoints only - no authentication required
    USE_PUBLIC_ENDPOINTS = True  # Forces use of public APIs
    
    # Rate limiting (to avoid being banned)
    REQUEST_DELAY = 1.0  # seconds between requests
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    # ============================================
    # OPEN API ENDPOINTS (No keys needed)
    # ============================================
    # Binance Public API
    BINANCE_PUBLIC_URL = "https://api.binance.com"
    BINANCE_OHLCV_ENDPOINT = "/api/v3/klines"
    BINANCE_TICKER_ENDPOINT = "/api/v3/ticker/24hr"
    BINANCE_ORDERBOOK_ENDPOINT = "/api/v3/depth"
    BINANCE_TRADES_ENDPOINT = "/api/v3/trades"
    
    # CoinGecko Public API (No key needed - 30 calls/min limit)
    COINGECKO_PUBLIC_URL = "https://api.coingecko.com/api/v3"
    COINGECKO_SIMPLE_PRICE = "/simple/price"
    COINGECKO_MARKET_DATA = "/coins/ethereum"
    COINGECKO_HISTORICAL = "/coins/ethereum/market_chart"
    COINGECKO_FEAR_GREED = "/fear_and_greed"
    
    # Deribit Public API (No key needed)
    DERIBIT_PUBLIC_URL = "https://www.deribit.com/api/v2"
    DERIBIT_OPTIONS_ENDPOINT = "/public/get_book_summary_by_instrument"
    DERIBIT_GREEKS_ENDPOINT = "/public/get_greeks"
    DERIBIT_VOLATILITY_ENDPOINT = "/public/get_volatility_index_data"
    
    # Etherscan Public API (No key needed for basic queries)
    ETHERSCAN_PUBLIC_URL = "https://api.etherscan.io/api"
    ETHERSCAN_ETH_PRICE = "?module=stats&action=ethprice"
    ETHERSCAN_ETH_SUPPLY = "?module=stats&action=ethsupply"
    ETHERSCAN_ACCOUNT_TX = "?module=account&action=txlist"
    
    # ============================================
    # TRADING SETTINGS
    # ============================================
    INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", 10000.0))
    POSITION_SIZE = float(os.getenv("POSITION_SIZE", 0.1))  # 10% of capital per trade
    MAX_POSITIONS = 3  # Maximum concurrent positions
    STOP_LOSS = 0.05  # 5% stop loss
    TAKE_PROFIT = 0.10  # 10% take profit
    
    # ============================================
    # MODEL SETTINGS
    # ============================================
    SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", 24))  # 24 hours for 1h timeframe
    TRAIN_SPLIT = float(os.getenv("TRAIN_SPLIT", 0.8))
    TEST_SPLIT = float(os.getenv("TEST_SPLIT", 0.1))
    VALIDATION_SPLIT = float(os.getenv("VALIDATION_SPLIT", 0.1))
    
    # LSTM specific
    LSTM_HIDDEN_SIZE = int(os.getenv("LSTM_HIDDEN_SIZE", 64))
    LSTM_NUM_LAYERS = int(os.getenv("LSTM_NUM_LAYERS", 2))
    LSTM_DROPOUT = float(os.getenv("LSTM_DROPOUT", 0.2))
    
    # Training
    EPOCHS = int(os.getenv("EPOCHS", 50))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 32))
    LEARNING_RATE = float(os.getenv("LEARNING_RATE", 0.001))
    EARLY_STOPPING_PATIENCE = int(os.getenv("EARLY_STOPPING_PATIENCE", 10))
    
    # ============================================
    # DATA COLLECTION SETTINGS
    # ============================================
    OHLCV_LIMIT = int(os.getenv("OHLCV_LIMIT", 500))  # Number of candles to fetch
    BACKFILL_DAYS = int(os.getenv("BACKFILL_DAYS", 30))  # Days to backfill
    
    # ============================================
    # SCHEDULER SETTINGS
    # ============================================
    UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", 60))
    MODEL_RETRAIN_HOURS = int(os.getenv("MODEL_RETRAIN_HOURS", 24))  # Retrain model daily
    
    # ============================================
    # LOGGING SETTINGS
    # ============================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = LOGS_DIR / "eth_bot.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5
    
    # ============================================
    # SIGNAL SETTINGS
    # ============================================
    SIGNAL_THRESHOLD = 0.02  # 2% minimum expected move to generate signal
    CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence to act on signal
    
    # ============================================
    # NOTIFICATION SETTINGS
    # ============================================
    ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "False").lower() == "true"
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "False").lower() == "true"
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")
    
    # ============================================
    # BACKTESTING SETTINGS
    # ============================================
    BACKTEST_START_DATE = os.getenv("BACKTEST_START_DATE", "2024-01-01")
    BACKTEST_END_DATE = os.getenv("BACKTEST_END_DATE", "2024-12-31")
    BACKTEST_COMMISSION = float(os.getenv("BACKTEST_COMMISSION", 0.001))  # 0.1%
    BACKTEST_SLIPPAGE = float(os.getenv("BACKTEST_SLIPPAGE", 0.001))  # 0.1%
    
    # ============================================
    # RISK MANAGEMENT
    # ============================================
    MAX_DRAWDOWN = float(os.getenv("MAX_DRAWDOWN", 0.20))  # 20% max drawdown
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", 0.02))  # 2% risk per trade
    MAX_LEVERAGE = int(os.getenv("MAX_LEVERAGE", 1))  # 1x = spot trading
    
    # ============================================
    # FEATURES FLAGS
    # ============================================
    ENABLE_LIVE_TRADING = os.getenv("ENABLE_LIVE_TRADING", "False").lower() == "true"
    ENABLE_PAPER_TRADING = os.getenv("ENABLE_PAPER_TRADING", "True").lower() == "true"
    ENABLE_BACKTESTING = os.getenv("ENABLE_BACKTESTING", "True").lower() == "true"
    ENABLE_MODEL_TRAINING = os.getenv("ENABLE_MODEL_TRAINING", "True").lower() == "true"
    ENABLE_DATA_COLLECTION = os.getenv("ENABLE_DATA_COLLECTION", "True").lower() == "true"
    
    # ============================================
    # DERIVED SETTINGS
    # ============================================
    @property
    def input_size(self):
        """Number of features for the model"""
        return 1  # Default: using only close price
    
    @property
    def output_size(self):
        """Number of outputs from the model"""
        return 1  # Predicting next price
    
    @property
    def device(self):
        """PyTorch device (CPU or GPU)"""
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except:
            return "cpu"
    
    # ============================================
    # VALIDATION
    # ============================================
    def validate(self):
        """Validate configuration settings"""
        assert self.SEQUENCE_LENGTH > 0, "SEQUENCE_LENGTH must be > 0"
        assert 0 < self.TRAIN_SPLIT < 1, "TRAIN_SPLIT must be between 0 and 1"
        assert 0 < self.POSITION_SIZE <= 1, "POSITION_SIZE must be between 0 and 1"
        assert self.STOP_LOSS > 0, "STOP_LOSS must be > 0"
        assert self.TAKE_PROFIT > self.STOP_LOSS, "TAKE_PROFIT must be > STOP_LOSS"
        
        if self.ENABLE_TELEGRAM:
            assert self.TELEGRAM_BOT_TOKEN, "TELEGRAM_BOT_TOKEN is required"
            assert self.TELEGRAM_CHAT_ID, "TELEGRAM_CHAT_ID is required"
        
        return True
    
    def get_api_info(self):
        """Display API information"""
        return {
            "status": "Using OPEN/PUBLIC APIs - No authentication required",
            "sources": [
                "Binance Public API (rate limit: 1200 requests/min)",
                "CoinGecko Public API (rate limit: 30 calls/min, no key needed)",
                "Deribit Public API (rate limit: 20 requests/sec)",
                "Etherscan Public API (rate limit: 1 request/sec)"
            ],
            "note": "For higher rate limits, add API keys in .env file"
        }
    
    def __repr__(self):
        """String representation of config"""
        api_info = self.get_api_info()
        return f"""
        ========================================
        ETH BOT FAST - CONFIGURATION
        ========================================
        Status: {api_info['status']}
        
        Symbol: {self.SYMBOL}
        Timeframe: {self.TIMEFRAME}
        Exchange: {self.EXCHANGE}
        
        Database: {self.DB_PATH}
        Data Directory: {self.DATA_DIR}
        Models Directory: {self.MODELS_DIR}
        Logs Directory: {self.LOGS_DIR}
        
        Initial Capital: ${self.INITIAL_CAPITAL:,.2f}
        Position Size: {self.POSITION_SIZE * 100}%
        Stop Loss: {self.STOP_LOSS * 100}%
        Take Profit: {self.TAKE_PROFIT * 100}%
        
        Sequence Length: {self.SEQUENCE_LENGTH}
        LSTM Hidden Size: {self.LSTM_HIDDEN_SIZE}
        LSTM Layers: {self.LSTM_NUM_LAYERS}
        Epochs: {self.EPOCHS}
        Learning Rate: {self.LEARNING_RATE}
        
        Device: {self.device}
        
        Live Trading: {self.ENABLE_LIVE_TRADING}
        Paper Trading: {self.ENABLE_PAPER_TRADING}
        Backtesting: {self.ENABLE_BACKTESTING}
        
        Update Interval: {self.UPDATE_INTERVAL_MINUTES} minutes
        Model Retrain: Every {self.MODEL_RETRAIN_HOURS} hours
        
        Data Sources:
        {chr(10).join(['  - ' + src for src in api_info['sources']])}
        ========================================
        """

# Create singleton instance
config = Config()

# Validate configuration on import
if __name__ != "__main__":
    config.validate()

# ============================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# ============================================
class DevelopmentConfig(Config):
    """Development environment settings"""
    ENABLE_LIVE_TRADING = False
    ENABLE_PAPER_TRADING = True
    ENABLE_BACKTESTING = True
    LOG_LEVEL = "DEBUG"
    UPDATE_INTERVAL_MINUTES = 5  # Update more frequently for testing

class ProductionConfig(Config):
    """Production environment settings"""
    ENABLE_LIVE_TRADING = True
    ENABLE_PAPER_TRADING = False
    ENABLE_BACKTESTING = False
    LOG_LEVEL = "WARNING"
    UPDATE_INTERVAL_MINUTES = 60

class TestingConfig(Config):
    """Testing environment settings"""
    ENABLE_LIVE_TRADING = False
    ENABLE_PAPER_TRADING = False
    ENABLE_BACKTESTING = True
    LOG_LEVEL = "DEBUG"
    DB_PATH = Config.DATA_DIR / "test_eth_bot.db"
    EPOCHS = 5  # Quick training for tests
    BATCH_SIZE = 16

# ============================================
# CONFIGURATION FACTORY
# ============================================
def get_config(env="development"):
    """
    Get configuration based on environment
    
    Args:
        env (str): Environment name ('development', 'production', 'testing')
    
    Returns:
        Config: Configuration instance
    """
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    
    return configs.get(env.lower(), DevelopmentConfig)()

# Example usage:
# config = get_config("production")