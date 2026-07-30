"""
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

from server.notebooks.ml_trading.data_prep import get_latest_data_for_prediction
from server.ml_trading.config import DB_PATH, MODEL_DIR, MIN_CONFIDENCE

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
    print("\n" + "=" * 60)
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
