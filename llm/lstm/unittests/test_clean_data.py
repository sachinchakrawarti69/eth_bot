import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.load_data import (
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

from llm.lstm.preprocessing.clean_data import clean_dataframe


datasets = {
    "OHLCV": load_ohlcv,
    "Orderbook": load_orderbook,
    "Trades": load_trades,
    "Funding Rate": load_funding_rate,
    "Open Interest": load_open_interest,
    "Option Chain": load_option_chain,
    "Greeks": load_greeks,
    "Implied Volatility": load_implied_volatility,
    "News": load_news,
    "Onchain": load_onchain,
    "Whales": load_whales,
    "Fear & Greed": load_fear_greed,
}

print("=" * 70)
print("TEST CLEAN DATA")
print("=" * 70)

for name, loader in datasets.items():

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    df = loader()

    print("Before Cleaning")

    print("Shape :", df.shape)

    cleaned = clean_dataframe(df)

    print("After Cleaning")

    print("Shape :", cleaned.shape)

    print()

    print(cleaned.dtypes)

    print()

    print(cleaned.head())