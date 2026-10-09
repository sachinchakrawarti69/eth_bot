"""Strategy definitions for the 6-year backtest."""

from __future__ import annotations


STRATEGIES = {
    "rsi_oversold_25": {
        "desc": "Buy when 1d RSI < 25, hold 14 days",
        "entry": lambda df: df["rsi_14"] < 25,
        "direction": "long",
        "hold_days": 14,
    },
    "rsi_oversold_30": {
        "desc": "Buy when 1d RSI < 30, hold 14 days",
        "entry": lambda df: df["rsi_14"] < 30,
        "direction": "long",
        "hold_days": 14,
    },
    "rsi_overbought_70": {
        "desc": "Short when 1d RSI > 70, hold 14 days",
        "entry": lambda df: df["rsi_14"] > 70,
        "direction": "short",
        "hold_days": 14,
    },
    "bull_dip": {
        "desc": "Buy when regime bull AND RSI < 40, hold 14 days",
        "entry": lambda df: (df["regime"] == "bull") & (df["rsi_14"] < 40),
        "direction": "long",
        "hold_days": 14,
    },
    "bear_rally": {
        "desc": "Short when regime bear AND RSI > 60, hold 14 days",
        "entry": lambda df: (df["regime"] == "bear") & (df["rsi_14"] > 60),
        "direction": "short",
        "hold_days": 14,
    },
    "trend_follow": {
        "desc": "Buy when regime bull AND MACD hist > 0, hold 30 days",
        "entry": lambda df: (df["regime"] == "bull") & (df["macd_hist"] > 0),
        "direction": "long",
        "hold_days": 30,
    },
    "fade_extended": {
        "desc": "Short when close > +15% from SMA50, hold 14 days",
        "entry": lambda df: df["dist_sma50"] > 0.15,
        "direction": "short",
        "hold_days": 14,
    },
    "buy_capitulation": {
        "desc": "Buy when vol_20 > 2x median AND RSI < 35, hold 14 days",
        "entry": lambda df: (df["vol_20"] > 2 * df["vol_20"].rolling(90).median()) & (df["rsi_14"] < 35),
        "direction": "long",
        "hold_days": 14,
    },
}
