"""
Web Dashboard using Flask
"""
from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd
from pathlib import Path
import json

app = Flask(__name__)
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'ETH.db'

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/price')
def get_price():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT date, close FROM eth_ohlcv ORDER BY date", conn)
    conn.close()
    
    return jsonify({
        'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
        'prices': df['close'].tolist()
    })

@app.route('/api/signals')
def get_signals():
    conn = sqlite3.connect(DB_PATH)
    signals = pd.read_sql("SELECT * FROM signals ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    
    return jsonify(signals.to_dict('records'))

@app.route('/api/performance')
def get_performance():
    conn = sqlite3.connect(DB_PATH)
    trades = pd.read_sql("SELECT * FROM trades", conn)
    conn.close()
    
    if len(trades) == 0:
        return jsonify({'total_trades': 0})
    
    return jsonify({
        'total_trades': len(trades),
        'winning_trades': len(trades[trades['pnl'] > 0]),
        'total_pnl': float(trades['pnl'].sum()),
        'win_rate': float(len(trades[trades['pnl'] > 0]) / len(trades) * 100)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)