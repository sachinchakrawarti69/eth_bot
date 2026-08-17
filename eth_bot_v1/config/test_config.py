"""
ETH Bot Configuration - Using Open APIs
"""

from pathlib import Path

class Config:
    """Main configuration"""
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Create directories
    for d in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Database
    DB_PATH = DATA_DIR / "eth_bot.db"
    
    # Trading
    SYMBOL = "ETH/USDT"
    TIMEFRAME = "1h"
    INITIAL_CAPITAL = 10000.0
    POSITION_SIZE = 0.1
    
    # Model
    SEQUENCE_LENGTH = 24
    
    # Features
    ENABLE_LIVE_TRADING = False
    ENABLE_PAPER_TRADING = True
    ENABLE_BACKTESTING = True
    
    @property
    def device(self):
        return "cpu"
    
    def __repr__(self):
        return f"""
        ========================================
        ETH BOT CONFIG
        ========================================
        Symbol: {self.SYMBOL}
        Database: {self.DB_PATH}
        Capital: ${self.INITIAL_CAPITAL}
        ========================================
        """

config = Config()