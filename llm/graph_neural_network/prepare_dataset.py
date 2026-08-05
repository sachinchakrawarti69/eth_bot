"""Create a time-safe single-asset GNN dataset from the project's OHLCV SQLite data.

With only ETHUSDT available this produces a one-node graph.  It validates the
training pipeline, but adding other symbols is necessary for relationship
learning between assets.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = (
    "open", "high", "low", "close", "volume", "log_return",
    "range_pct", "body_pct", "volume_change", "sma_7_ratio", "rsi_14",
)


def load_features(database: Path, symbol: str, interval: str) -> tuple[np.ndarray, np.ndarray]:
    """Return engineered features and next-candle returns ordered by time."""
    query = """
        SELECT open_time, open, high, low, close, volume
        FROM ohlcv
        WHERE symbol = ? AND interval = ?
        ORDER BY open_time
    """
    with sqlite3.connect(database) as connection:
        frame = pd.read_sql_query(query, connection, params=(symbol, interval))
    if frame.empty:
        raise ValueError(f"No candles found for {symbol} at interval {interval!r}")

    frame["log_return"] = np.log(frame["close"] / frame["close"].shift(1))
    frame["range_pct"] = (frame["high"] - frame["low"]) / frame["close"]
    frame["body_pct"] = (frame["close"] - frame["open"]) / frame["open"]
    frame["volume_change"] = frame["volume"].pct_change()
    frame["sma_7_ratio"] = frame["close"] / frame["close"].rolling(7).mean() - 1.0
    delta = frame["close"].diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    relative_strength = gain.rolling(14).mean() / loss.rolling(14).mean()
    frame["rsi_14"] = 100.0 - 100.0 / (1.0 + relative_strength)
    frame["target"] = frame["close"].shift(-1) / frame["close"] - 1.0
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    if len(frame) < 50:
        raise ValueError("At least 50 valid candles are required after feature engineering")
    return frame.loc[:, FEATURE_COLUMNS].to_numpy(np.float32), frame["target"].to_numpy(np.float32)


def save_dataset(features: np.ndarray, targets: np.ndarray, output: Path) -> None:
    """Time-split features, fit scaling only on training data, and save arrays."""
    train_end = int(len(features) * 0.70)
    validation_end = int(len(features) * 0.85)
    scaler = StandardScaler().fit(features[:train_end])
    scaled = scaler.transform(features).astype(np.float32)
    output.mkdir(parents=True, exist_ok=True)
    splits = {
        "train": slice(None, train_end),
        "validation": slice(train_end, validation_end),
    }
    for name, selection in splits.items():
        node_features = scaled[selection, np.newaxis, :]
        adjacency = np.ones((len(node_features), 1, 1), dtype=np.float32)
        np.save(output / f"nodes_{name}.npy", node_features)
        np.save(output / f"edges_{name}.npy", adjacency)
        np.save(output / f"y_{name}.npy", targets[selection, np.newaxis])
    print(f"Saved {train_end} training and {validation_end - train_end} validation samples to {output}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Create GNN arrays from SQLite OHLCV candles.")
    parser.add_argument("--database", type=Path, default=root / "storage" / "database" / "eth.db")
    parser.add_argument("--output", type=Path, default=root / "data" / "gnn")
    parser.add_argument("--symbol", default="ETHUSDT")
    parser.add_argument("--interval", default="1d")
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error(f"Database does not exist: {args.database}")
    features, targets = load_features(args.database, args.symbol, args.interval)
    save_dataset(features, targets, args.output)


if __name__ == "__main__":
    main()
