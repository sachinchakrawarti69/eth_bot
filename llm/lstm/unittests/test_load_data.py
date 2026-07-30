import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.load_data import (
    dataset_summary,
    load_ohlcv,
    load_orderbook,
    load_trades,
    load_funding_rate,
    load_open_interest,
    load_option_chain,
    load_greeks,
    load_implied_volatility,
    load_news,
    load_onchain,
    load_whales,
    load_fear_greed,
)

print("=" * 60)
print("TESTING LOAD DATA")
print("=" * 60)

# ---------------------------------------------------------
# Database Summary
# ---------------------------------------------------------

dataset_summary()

# ---------------------------------------------------------
# Tables
# ---------------------------------------------------------

tables = {
    "OHLCV": load_ohlcv(),
    "Orderbook": load_orderbook(),
    "Trades": load_trades(),
    "Funding Rate": load_funding_rate(),
    "Open Interest": load_open_interest(),
    "Option Chain": load_option_chain(),
    "Greeks": load_greeks(),
    "Implied Volatility": load_implied_volatility(),
    "News": load_news(),
    "Onchain": load_onchain(),
    "Whales": load_whales(),
    "Fear & Greed": load_fear_greed(),
}

# ---------------------------------------------------------
# Print Summary
# ---------------------------------------------------------

for name, df in tables.items():

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print("Rows    :", len(df))
    print("Columns :", len(df.columns))
    print("Shape   :", df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 Rows:")
    print(df.head())