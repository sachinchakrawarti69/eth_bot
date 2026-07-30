"""
Main trading bot
"""
import time
import schedule
import logging
import sys
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))

from server.ml_trading.config import USE_TESTNET, LOG_FILE
from server.ml_trading.predict import SignalGenerator
from server.ml_trading.trade_executor import execute_trade
from server.ml_trading.trade_logger import TradeLogger

class TradingBot:
    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.logger = TradeLogger()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
            handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
        self.log = logging.getLogger(__name__)
        self.log.info("Bot Started")
    
    def run_trading_cycle(self):
        self.log.info("=" * 60)
        self.log.info(f"Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log.info("=" * 60)
        
        signal = self.signal_generator.get_signal()
        self.log.info(f"Signal: {signal['signal_type']} (Conf: {signal['confidence']:.2%})")
        self.log.info(f"{signal['recommendation']}")
        self.signal_generator.save_signal_to_db(signal)
        
        from server.ml_trading.config import MIN_CONFIDENCE
        if signal['signal_type'] == 'BUY' and signal['confidence'] >= MIN_CONFIDENCE:
            self.log.info("Executing BUY...")
            execute_trade('BUY')
        elif signal['signal_type'] == 'SELL' and signal['confidence'] >= MIN_CONFIDENCE:
            self.log.info("Executing SELL...")
            execute_trade('SELL')
        else:
            self.log.info("No action")
        self.log.info("=" * 60 + "\n")
    
    def run_continuously(self, interval_minutes=60):
        self.log.info(f"Running every {interval_minutes} min")
        self.run_trading_cycle()
        schedule.every(interval_minutes).minutes.do(self.run_trading_cycle)
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    print("=" * 60)
    print("ETH ML Trading Bot")
    print(f"Testnet: {USE_TESTNET}")
    print("=" * 60)
    bot = TradingBot()
    bot.run_trading_cycle()

if __name__ == "__main__":
    main()
