"""Generate daily analysis report."""
from __future__ import annotations
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT      = Path(__file__).resolve().parents[1]
DB        = ROOT / "database" / "market.db"
OUT_DIR   = ROOT / "reports" / "daily"
SYMBOL    = "ETHUSDT"
TIMEFRAME = "1d"


def load():
    with sqlite3.connect(DB) as c:
        df = pd.read_sql_query(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlcv WHERE symbol=? AND timeframe=? ORDER BY open_time",
            c, params=(SYMBOL, TIMEFRAME))
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.set_index("date").drop(columns=["open_time"])

    df["return"] = df["close"].pct_change()
    df["sma_50"]  = df["close"].rolling(50).mean()
    df["sma_200"] = df["close"].rolling(200).mean()
    d  = df["close"].diff()
    up = d.clip(lower=0).rolling(14).mean()
    dn = (-d.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    tr = pd.concat([df.high - df.low,
                    (df.high - df.close.shift()).abs(),
                    (df.low  - df.close.shift()).abs()], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    return df.dropna()


def main():
    df = load()
    last = df.iloc[-1]
    r = df["return"].dropna()
    cum = (1 + r).cumprod()
    dd = (cum / cum.cummax() - 1).min()

    today = date.today().isoformat()
    out = OUT_DIR / today
    out.mkdir(parents=True, exist_ok=True)

    stats = {
        "start":         df.index.min().date().isoformat(),
        "end":           df.index.max().date().isoformat(),
        "days":          len(df),
        "total_return":  float(cum.iloc[-1] - 1),
        "ann_vol":       float(r.std(ddof=0) * np.sqrt(365)),
        "sharpe":        float(r.mean() / r.std(ddof=0) * np.sqrt(365)),
        "max_drawdown":  float(dd),
        "best_day":      float(r.max()),
        "worst_day":     float(r.min()),
        "last_close":    float(last.close),
        "last_sma_50":   float(last.sma_50),
        "last_sma_200":  float(last.sma_200),
        "last_rsi":      float(last.rsi_14),
        "last_atr":      float(last.atr_14),
    }

    lines = [
        f"# {SYMBOL} daily report - {today}",
        "",
        "## Summary",
        f"- Period: {stats['start']} to {stats['end']}",
        f"- Days: {stats['days']}",
        f"- Total return: {stats['total_return']:+.2%}",
        f"- Annualized vol: {stats['ann_vol']:.2%}",
        f"- Sharpe (0 rf): {stats['sharpe']:.2f}",
        f"- Max drawdown: {stats['max_drawdown']:.2%}",
        f"- Best day: {stats['best_day']:+.2%}",
        f"- Worst day: {stats['worst_day']:+.2%}",
        "",
        "## Latest",
        f"- Close: {stats['last_close']:.2f}",
        f"- SMA50: {stats['last_sma_50']:.2f}",
        f"- SMA200: {stats['last_sma_200']:.2f}",
        f"- RSI(14): {stats['last_rsi']:.2f}",
        f"- ATR(14): {stats['last_atr']:.2f}",
    ]

    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    import json
    (out / "summary.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"  wrote {out / 'summary.md'}")
    print(f"  wrote {out / 'summary.json'}")


if __name__ == "__main__":
    main()
