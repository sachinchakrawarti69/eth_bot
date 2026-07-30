"""
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

from server.ml_trading.config import (
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
    print("\n" + "=" * 60)
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
