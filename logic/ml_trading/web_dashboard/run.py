
"""
Run Web Dashboard
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from server.ml_trading.web_dashboard.app import app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ETH Trading Dashboard")
    print("=" * 60)
    print("🌐 Server: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)