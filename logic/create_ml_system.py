"""
Create complete ML Trading System - All files in one script
Run this once to create all necessary files
"""
import os
from pathlib import Path

# ============================================
# CREATE DIRECTORY STRUCTURE
# ============================================
BASE_DIR = Path(__file__).parent
ML_DIR = BASE_DIR / 'ml_trading'

# Create ml_trading directory
ML_DIR.mkdir(exist_ok=True)

print("=" * 60)
print("Creating ML Trading System")
print("=" * 60)
print(f"Base Directory: {BASE_DIR}")
print(f"ML Directory: {ML_DIR}")

# ============================================
# FILE 1: __init__.py
# ============================================
print("\nCreating __init__.py...")
with open(ML_DIR / '__init__.py', 'w', encoding='utf-8') as f:
    f.write('"""ML Trading Bot for Ethereum"""\n__version__ = "1.0.0"\n')

# ============================================
# FILE 2: config.py
# ============================================
print("Creating config.py...")
config_content = '''"""
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
'''
with open(ML_DIR / 'config.py', 'w', encoding='utf-8') as f:
    f.write(config_content)

# ============================================
# FILE 3: data_prep.py
# ============================================
print("Creating data_prep.py...")
data_prep_content = '''"""
Data preparation for ML models
"""
import pandas as pd
import sqlite3
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ml_trading.config import DB_PATH, FEATURES

def load_data_from_sqlite():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM eth_ohlcv ORDER BY date", conn, parse_dates=['date'])
        conn.close()
        print(f"Loaded {len(df)} days of data from SQLite")
        return df
    except:
        csv_path = Path(__file__).parent.parent / 'data' / 'Eth_OHLCV.csv'
        if csv_path.exists():
            df = pd.read_csv(csv_path, parse_dates=['date'])
            print(f"Loaded {len(df)} days of data from CSV")
            return df
        print("No data found")
        return None

def add_technical_indicators(df):
    if df is None or len(df) == 0:
        return None
    df = df.copy()
    df['SMA_7'] = df['close'].rolling(7).mean()
    df['SMA_20'] = df['close'].rolling(20).mean()
    df['SMA_50'] = df['close'].rolling(50).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['BB_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR_14'] = true_range.rolling(14).mean()
    return df

def create_target_variable(df, days_ahead=1):
    if df is None or len(df) == 0:
        return None
    df = df.copy()
    df['future_close'] = df['close'].shift(-days_ahead)
    df['target'] = df['future_close'] / df['close'] - 1
    df['target_class'] = 0
    df.loc[df['target'] > 0.01, 'target_class'] = 1
    df.loc[df['target'] < -0.01, 'target_class'] = 2
    return df

def prepare_ml_data(df):
    if df is None:
        return None, None, None, None, None
    df = add_technical_indicators(df)
    df = create_target_variable(df)
    df = df.dropna()
    if len(df) < 100:
        print("Not enough data for ML")
        return None, None, None, None, None
    X = df[FEATURES]
    y = df['target_class']
    split_idx = int(len(df) * 0.8)
    X_train = X[:split_idx]
    X_test = X[split_idx:]
    y_train = y[:split_idx]
    y_test = y[split_idx:]
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    return X_train, X_test, y_train, y_test, df

def get_latest_data_for_prediction():
    df = load_data_from_sqlite()
    if df is None:
        return None, None
    df = add_technical_indicators(df)
    df = df.dropna()
    latest = df[FEATURES].iloc[-1:].values.reshape(1, -1)
    return latest, df
'''
with open(ML_DIR / 'data_prep.py', 'w', encoding='utf-8') as f:
    f.write(data_prep_content)

# ============================================
# FILE 4: train_model.py
# ============================================
print("Creating train_model.py...")
train_model_content = '''"""
Train ML models for ETH price prediction
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ml_trading.data_prep import load_data_from_sqlite, prepare_ml_data
from ml_trading.config import MODEL_DIR, FEATURES

class MLTradingModel:
    def __init__(self):
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.best_accuracy = 0
        self.model_path = MODEL_DIR
    
    def train_models(self, X_train, y_train):
        print("\\nTraining ML models...")
        print("-" * 40)
        
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        self.models['RandomForest'] = rf
        print("Random Forest trained")
        
        gb = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
        gb.fit(X_train, y_train)
        self.models['GradientBoosting'] = gb
        print("Gradient Boosting trained")
        
        try:
            import xgboost as xgb
            xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)
            self.models['XGBoost'] = xgb_model
            print("XGBoost trained")
        except:
            print("XGBoost not available")
        
        try:
            import lightgbm as lgb
            lgb_model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            lgb_model.fit(X_train, y_train)
            self.models['LightGBM'] = lgb_model
            print("LightGBM trained")
        except:
            print("LightGBM not available")
        
        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(X_train, y_train)
        self.models['LogisticRegression'] = lr
        print("Logistic Regression trained")
    
    def evaluate_models(self, X_test, y_test):
        print("\\nModel Evaluation:")
        print("-" * 40)
        results = {}
        for name, model in self.models.items():
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            results[name] = accuracy
            print(f"   {name}: {accuracy:.4f}")
        best_name = max(results, key=results.get)
        self.best_model = self.models[best_name]
        self.best_model_name = best_name
        self.best_accuracy = results[best_name]
        print(f"\\nBest: {best_name} ({results[best_name]:.4f})")
        return results
    
    def save_best_model(self):
        if self.best_model:
            model_file = self.model_path / f"{self.best_model_name}_model.pkl"
            joblib.dump(self.best_model, model_file)
            print(f"Model saved to: {model_file}")
    
    def plot_confusion_matrix(self, X_test, y_test):
        if self.best_model is None:
            return
        y_pred = self.best_model.predict(X_test)
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title(f'Confusion Matrix - {self.best_model_name}')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.tight_layout()
        plt.savefig(self.model_path / 'confusion_matrix.png')
        plt.show()

def main():
    print("=" * 60)
    print("Training ML Models")
    print("=" * 60)
    df = load_data_from_sqlite()
    if df is None:
        return
    X_train, X_test, y_train, y_test, _ = prepare_ml_data(df)
    if X_train is None:
        return
    trainer = MLTradingModel()
    trainer.train_models(X_train, y_train)
    trainer.evaluate_models(X_test, y_test)
    trainer.save_best_model()
    trainer.plot_confusion_matrix(X_test, y_test)
    print("\\nTraining complete!")

if __name__ == "__main__":
    main()
'''
with open(ML_DIR / 'train_model.py', 'w', encoding='utf-8') as f:
    f.write(train_model_content)

# ============================================
# FILE 5: predict.py
# ============================================
print("Creating predict.py...")
predict_content = '''"""
Generate trading signals using trained ML models
"""
import pandas as pd
import numpy as np
import sqlite3
import joblib
from pathlib import Path
import datetime
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ml_trading.data_prep import get_latest_data_for_prediction
from ml_trading.config import DB_PATH, MODEL_DIR, MIN_CONFIDENCE

class SignalGenerator:
    def __init__(self):
        self.model_path = MODEL_DIR
        self.model = None
        self.model_name = None
        self.load_model()
        self.last_signal = None
    
    def load_model(self):
        model_files = list(self.model_path.glob('*_model.pkl'))
        if not model_files:
            print("No model found. Train first.")
            self.model = None
            return
        self.model = joblib.load(model_files[0])
        self.model_name = model_files[0].stem.replace('_model', '')
        print(f"Loaded model: {model_files[0].name}")
    
    def get_signal(self):
        if self.model is None:
            return {'signal': 0, 'signal_type': 'HOLD', 'confidence': 0, 'message': 'No model loaded'}
        
        latest_data, df = get_latest_data_for_prediction()
        if latest_data is None:
            return {'signal': 0, 'signal_type': 'HOLD', 'confidence': 0, 'message': 'No data'}
        
        prediction = self.model.predict(latest_data)[0]
        probabilities = self.model.predict_proba(latest_data)[0]
        confidence = max(probabilities)
        current_price = df['close'].iloc[-1]
        
        signal_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
        signal_type = signal_map.get(prediction, 'HOLD')
        
        if confidence < MIN_CONFIDENCE:
            signal_type = 'HOLD'
            confidence = 0
        
        if signal_type == 'BUY':
            recommendation = f"BUY at ${current_price:.2f} (Conf: {confidence:.2%})"
        elif signal_type == 'SELL':
            recommendation = f"SELL at ${current_price:.2f} (Conf: {confidence:.2%})"
        else:
            recommendation = f"HOLD at ${current_price:.2f}"
        
        result = {
            'signal': prediction,
            'signal_type': signal_type,
            'confidence': confidence,
            'current_price': current_price,
            'recommendation': recommendation,
            'timestamp': datetime.datetime.now().isoformat(),
            'model': self.model_name
        }
        self.last_signal = result
        return result
    
    def save_signal_to_db(self, signal_result):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("CREATE TABLE IF NOT EXISTS signals (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, signal INTEGER, signal_type TEXT, confidence REAL, current_price REAL, recommendation TEXT, model TEXT)")
            conn.execute("INSERT INTO signals (timestamp, signal, signal_type, confidence, current_price, recommendation, model) VALUES (?, ?, ?, ?, ?, ?, ?)", (
                signal_result['timestamp'], signal_result['signal'], signal_result['signal_type'],
                signal_result['confidence'], signal_result['current_price'],
                signal_result['recommendation'], signal_result.get('model', 'Unknown')
            ))
            conn.commit()
            conn.close()
            print("Signal saved")
        except Exception as e:
            print(f"Error: {e}")

def generate_signal():
    generator = SignalGenerator()
    signal = generator.get_signal()
    print("\\n" + "=" * 60)
    print(f"Signal - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Price: ${signal['current_price']:.2f}")
    print(f"Signal: {signal['signal_type']}")
    print(f"Confidence: {signal['confidence']:.2%}")
    print(f"{signal['recommendation']}")
    print("=" * 60)
    generator.save_signal_to_db(signal)
    return signal

if __name__ == "__main__":
    generate_signal()
'''
with open(ML_DIR / 'predict.py', 'w', encoding='utf-8') as f:
    f.write(predict_content)

# ============================================
# FILE 6: trade_executor.py
# ============================================
print("Creating trade_executor.py...")
trade_executor_content = '''"""
Execute trades using Binance API
"""
import time
import hmac
import hashlib
import requests
import logging
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ml_trading.config import (
    BINANCE_API_KEY, BINANCE_SECRET_KEY, USE_TESTNET,
    SYMBOL, QUANTITY, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, MAX_DAILY_TRADES
)

class BinanceTrader:
    def __init__(self):
        self.api_key = BINANCE_API_KEY
        self.secret_key = BINANCE_SECRET_KEY
        if USE_TESTNET or BINANCE_API_KEY == "YOUR_API_KEY_HERE":
            self.base_url = "https://testnet.binance.vision"
            print("Using TESTNET")
        else:
            self.base_url = "https://api.binance.com"
            print("Using REAL Binance")
        self.symbol = SYMBOL
        self.quantity = QUANTITY
        self.position = 0
        self.entry_price = 0
        self.trades_today = 0
        self.last_trade_date = None
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _create_signature(self, params):
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        return hmac.new(self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def _make_request(self, method, endpoint, params=None):
        if params is None:
            params = {}
        params['timestamp'] = int(time.time() * 1000)
        params['recvWindow'] = 5000
        params['signature'] = self._create_signature(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}{endpoint}"
        try:
            if method == 'GET':
                r = requests.get(url, params=params, headers=headers)
            else:
                r = requests.post(url, params=params, headers=headers)
            return r.json()
        except Exception as e:
            self.logger.error(f"API error: {e}")
            return None
    
    def get_account_balance(self):
        response = self._make_request('GET', '/api/v3/account')
        if response and 'balances' in response:
            balances = {}
            for asset in response['balances']:
                if float(asset['free']) > 0 or float(asset['locked']) > 0:
                    balances[asset['asset']] = {
                        'free': float(asset['free']),
                        'locked': float(asset['locked']),
                        'total': float(asset['free']) + float(asset['locked'])
                    }
            return balances
        return {}
    
    def get_current_price(self):
        try:
            r = requests.get(f"{self.base_url}/api/v3/ticker/price", params={'symbol': self.symbol})
            return float(r.json()['price'])
        except:
            return 0
    
    def place_order(self, side, quantity=None):
        if quantity is None:
            quantity = self.quantity
        params = {'symbol': self.symbol, 'side': side.upper(), 'type': 'MARKET', 'quantity': quantity}
        return self._make_request('POST', '/api/v3/order', params)
    
    def buy(self):
        if self.position == 1:
            self.logger.warning("Already in position")
            return None
        if not self._can_trade():
            return None
        balances = self.get_account_balance()
        usdt = balances.get('USDT', {}).get('free', 0)
        price = self.get_current_price()
        max_qty = (usdt * 0.95) / price if price > 0 else 0
        if max_qty < self.quantity:
            self.logger.warning(f"Insufficient: {usdt:.2f} USDT")
            return None
        order = self.place_order('BUY')
        if order and 'orderId' in order:
            self.position = 1
            self.entry_price = self.get_current_price()
            self.trades_today += 1
            self.last_trade_date = datetime.now().date()
            self.logger.info(f"Bought {self.quantity} ETH at ${self.entry_price:.2f}")
            return order
        return None
    
    def sell(self):
        if self.position == 0:
            self.logger.warning("No position")
            return None
        if not self._can_trade():
            return None
        order = self.place_order('SELL')
        if order and 'orderId' in order:
            sell_price = self.get_current_price()
            self.position = 0
            pnl = (sell_price - self.entry_price) * self.quantity
            pnl_pct = (sell_price / self.entry_price - 1) * 100 if self.entry_price > 0 else 0
            self.trades_today += 1
            self.last_trade_date = datetime.now().date()
            self.logger.info(f"Sold at ${sell_price:.2f}, P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
            return order
        return None
    
    def _can_trade(self):
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.trades_today = 0
            self.last_trade_date = today
            return True
        return self.trades_today < MAX_DAILY_TRADES
    
    def get_position_info(self):
        if self.position == 0:
            return {'in_position': False}
        price = self.get_current_price()
        pnl = (price / self.entry_price - 1) * 100 if self.entry_price > 0 else 0
        return {'in_position': True, 'entry_price': self.entry_price, 'current_price': price, 'pnl_percent': pnl}
    
    def close_position(self):
        if self.position == 0:
            return False
        price = self.get_current_price()
        if self.entry_price == 0:
            return False
        pnl = (price / self.entry_price - 1) * 100
        if pnl <= -STOP_LOSS_PERCENT * 100:
            self.logger.warning(f"Stop loss at {pnl:.2f}%")
            self.sell()
            return True
        if pnl >= TAKE_PROFIT_PERCENT * 100:
            self.logger.info(f"Take profit at {pnl:.2f}%")
            self.sell()
            return True
        return False

def execute_trade(signal_type):
    trader = BinanceTrader()
    print("\\n" + "=" * 60)
    print(f"Trade - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    pos = trader.get_position_info()
    if pos['in_position']:
        print(f"In position: Entry ${pos['entry_price']:.2f}, P&L: {pos['pnl_percent']:.2f}%")
    result = None
    if signal_type == 'BUY' and not pos['in_position']:
        result = trader.buy()
    elif signal_type == 'SELL' and pos['in_position']:
        result = trader.sell()
    else:
        print("No action")
    print("Done" if result else "Failed")
    print("=" * 60)
    return result

if __name__ == "__main__":
    execute_trade('BUY')
'''
with open(ML_DIR / 'trade_executor.py', 'w', encoding='utf-8') as f:
    f.write(trade_executor_content)

# ============================================
# FILE 7: trade_logger.py
# ============================================
print("Creating trade_logger.py...")
trade_logger_content = '''"""
Log trades to SQLite database
"""
import sqlite3
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from ml_trading.config import DB_PATH

class TradeLogger:
    def __init__(self):
        self.db_path = DB_PATH
        self.create_tables()
    
    def create_tables(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, type TEXT, price REAL, quantity REAL, order_id TEXT, pnl REAL, pnl_percent REAL, signal_confidence REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS performance (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, total_trades INTEGER, winning_trades INTEGER, losing_trades INTEGER, total_pnl REAL, win_rate REAL, balance REAL)")
            conn.commit()
            conn.close()
            print("Trade tables created")
        except Exception as e:
            print(f"Error: {e}")
    
    def log_trade(self, trade_data):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO trades (timestamp, type, price, quantity, order_id, pnl, pnl_percent, signal_confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                trade_data.get('timestamp', datetime.now().isoformat()),
                trade_data.get('type'), trade_data.get('price', 0),
                trade_data.get('quantity', 0), trade_data.get('order_id', ''),
                trade_data.get('pnl', 0), trade_data.get('pnl_percent', 0),
                trade_data.get('signal_confidence', 0)
            ))
            conn.commit()
            conn.close()
            print("Trade logged")
        except Exception as e:
            print(f"Error: {e}")
    
    def get_trade_history(self, limit=100):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql(f"SELECT * FROM trades ORDER BY id DESC LIMIT {limit}", conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()
    
    def get_performance_summary(self):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql("SELECT * FROM trades", conn)
            conn.close()
            if len(df) == 0:
                return {'total_trades': 0}
            return {
                'total_trades': len(df),
                'winning_trades': len(df[df['pnl'] > 0]),
                'losing_trades': len(df[df['pnl'] < 0]),
                'total_pnl': df['pnl'].sum() if 'pnl' in df else 0,
                'win_rate': len(df[df['pnl'] > 0]) / len(df) * 100 if len(df) > 0 else 0
            }
        except:
            return {'total_trades': 0}

if __name__ == "__main__":
    logger = TradeLogger()
    test = {'timestamp': datetime.now().isoformat(), 'type': 'BUY', 'price': 3000, 'quantity': 0.001, 'order_id': '123'}
    logger.log_trade(test)
    print(logger.get_trade_history())
'''
with open(ML_DIR / 'trade_logger.py', 'w', encoding='utf-8') as f:
    f.write(trade_logger_content)

# ============================================
# FILE 8: run_trading.py
# ============================================
print("Creating run_trading.py...")
run_trading_content = '''"""
Main trading bot
"""
import time
import schedule
import logging
import sys
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))

from ml_trading.config import USE_TESTNET, LOG_FILE
from ml_trading.predict import SignalGenerator
from ml_trading.trade_executor import execute_trade
from ml_trading.trade_logger import TradeLogger

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
        
        from ml_trading.config import MIN_CONFIDENCE
        if signal['signal_type'] == 'BUY' and signal['confidence'] >= MIN_CONFIDENCE:
            self.log.info("Executing BUY...")
            execute_trade('BUY')
        elif signal['signal_type'] == 'SELL' and signal['confidence'] >= MIN_CONFIDENCE:
            self.log.info("Executing SELL...")
            execute_trade('SELL')
        else:
            self.log.info("No action")
        self.log.info("=" * 60 + "\\n")
    
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
'''
with open(ML_DIR / 'run_trading.py', 'w', encoding='utf-8') as f:
    f.write(run_trading_content)

# ============================================
# FILE 9: requirements.txt
# ============================================
print("Creating requirements.txt...")
with open(BASE_DIR / 'requirements.txt', 'w', encoding='utf-8') as f:
    f.write('''pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0
seaborn>=0.11.0
scikit-learn>=0.24.0
xgboost>=1.4.0
lightgbm>=3.2.0
python-binance>=1.0.0
schedule>=1.1.0
plotly>=5.0.0
joblib>=1.1.0
requests>=2.26.0
''')

# ============================================
# FILE 10: README_ML.md
# ============================================
print("Creating README_ML.md...")
with open(BASE_DIR / 'README_ML.md', 'w', encoding='utf-8') as f:
    f.write('''# ETH ML Trading Bot

## Quick Start
1. `pip install -r requirements.txt`
2. Edit `ml_trading/config.py` with API keys
3. `python collect_eth_daily.py`
4. `cd ml_trading && python train_model.py`
5. `python predict.py`
6. `python run_trading.py`

## Test Mode
Set `USE_TESTNET = True` in config.py

## Disclaimer
Use at your own risk. Educational purposes only.
''')

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 60)
print("ALL FILES CREATED SUCCESSFULLY!")
print("=" * 60)
print("\nCreated Files:")
for file in ML_DIR.glob('*.py'):
    size = file.stat().st_size
    print(f"   - {file.name} ({size} bytes)")

print(f"\nRequirements: {BASE_DIR / 'requirements.txt'}")
print(f"README: {BASE_DIR / 'README_ML.md'}")

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print("1. pip install -r requirements.txt")
print("2. Edit ml_trading/config.py with your API keys")
print("3. python collect_eth_daily.py")
print("4. cd ml_trading && python train_model.py")
print("5. python predict.py")
print("6. python run_trading.py")
print("=" * 60)