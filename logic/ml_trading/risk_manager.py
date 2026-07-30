"""
Advanced Risk Management
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

db_path = Path('..') / 'data' / 'ETH.db'

class RiskManager:
    def __init__(self):
        self.max_daily_loss = 0.05  # 5% max daily loss
        self.max_position_size = 0.01  # 0.01 ETH max
        self.max_drawdown = 0.10  # 10% max drawdown
    
    def get_daily_pnl(self):
        """Get today's P&L"""
        conn = sqlite3.connect(db_path)
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        
        trades = conn.execute("""
            SELECT SUM(pnl) as total_pnl FROM trades 
            WHERE date(timestamp) = ?
        """, (today_str,)).fetchone()
        
        conn.close()
        return trades[0] if trades[0] else 0
    
    def get_total_drawdown(self):
        """Calculate current drawdown"""
        conn = sqlite3.connect(db_path)
        trades = conn.execute("SELECT pnl FROM trades ORDER BY id").fetchall()
        conn.close()
        
        if not trades:
            return 0
        
        pnls = [t[0] for t in trades if t[0] is not None]
        if not pnls:
            return 0
        
        cumulative = []
        running = 0
        for pnl in pnls:
            running += pnl
            cumulative.append(running)
        
        peak = max(cumulative)
        current = cumulative[-1]
        drawdown = (peak - current) / peak if peak > 0 else 0
        
        return drawdown
    
    def can_trade(self):
        """Check if we can trade"""
        # Check daily loss
        daily_pnl = self.get_daily_pnl()
        if daily_pnl < -self.max_daily_loss * 1000:  # Assuming $1000 initial balance
            print(f"⚠️ Daily loss limit reached: ${daily_pnl:.2f}")
            return False
        
        # Check drawdown
        drawdown = self.get_total_drawdown()
        if drawdown > self.max_drawdown:
            print(f"⚠️ Max drawdown reached: {drawdown:.1%}")
            return False
        
        return True
    
    def get_position_size(self, base_size=0.001):
        """Calculate position size based on risk"""
        if not self.can_trade():
            return 0
        
        # Reduce size if losing
        drawdown = self.get_total_drawdown()
        if drawdown > 0.05:
            return base_size * 0.5
        elif drawdown > 0.08:
            return base_size * 0.25
        
        return base_size

if __name__ == "__main__":
    rm = RiskManager()
    print(f"Can Trade: {rm.can_trade()}")
    print(f"Position Size: {rm.get_position_size()} ETH")