"""Build the features table.

Reads ohlcv (1h, 4h, 1d), funding_rate, open_interest,
long_short_ratio, taker_volume. Computes indicators, aligns
everything to the 1h clock, writes to `features`.

Usage:
    python -m scripts_python.build_features
    python -m scripts_python.build_features --symbols BTCUSDT,ETHUSDT
    python -m scripts_python.build_features --full       # drop + rebuild
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "market.db"

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]


# ------------------------------------------------------------------
# loading
# ------------------------------------------------------------------

def load_ohlcv(conn, symbol, timeframe, limit=None):
    q = ("SELECT open_time, open, high, low, close, volume "
         "FROM ohlcv WHERE symbol=? AND timeframe=? ORDER BY open_time")
    df = pd.read_sql_query(q, conn, params=(symbol, timeframe))
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.drop(columns=["open_time"]).set_index("date")
    return df


def load_funding(conn, symbol):
    try:
        df = pd.read_sql_query(
            "SELECT ts, rate FROM funding_rate WHERE symbol=? ORDER BY ts",
            conn, params=(symbol,))
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(None)
    return df.drop(columns=["ts"]).set_index("date")


def load_oi(conn, symbol):
    try:
        df = pd.read_sql_query(
            "SELECT ts, oi FROM open_interest WHERE symbol=? ORDER BY ts",
            conn, params=(symbol,))
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(None)
    return df.drop(columns=["ts"]).set_index("date")


def load_ls(conn, symbol):
    try:
        df = pd.read_sql_query(
            "SELECT ts, ratio FROM long_short_ratio WHERE symbol=? ORDER BY ts",
            conn, params=(symbol,))
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(None)
    return df.drop(columns=["ts"]).set_index("date")


def load_taker(conn, symbol):
    try:
        df = pd.read_sql_query(
            "SELECT ts, buy_ratio FROM taker_volume WHERE symbol=? ORDER BY ts",
            conn, params=(symbol,))
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(None)
    return df.drop(columns=["ts"]).set_index("date")


# ------------------------------------------------------------------
# indicators
# ------------------------------------------------------------------

def add_indicators(df):
    """Add RSI, MACD, ATR, SMAs, returns to a candle dataframe."""
    df = df.copy()

    # returns
    df["ret_1"]  = df["close"].pct_change(1)
    df["ret_5"]  = df["close"].pct_change(5)
    df["ret_20"] = df["close"].pct_change(20)
    df["vol_20"] = df["ret_1"].rolling(20).std()

    # SMAs / EMAs
    df["sma_20"]  = df["close"].rolling(20).mean()
    df["sma_50"]  = df["close"].rolling(50).mean()
    df["sma_200"] = df["close"].rolling(200).mean()
    df["ema_12"]  = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"]  = df["close"].ewm(span=26, adjust=False).mean()

    # MACD histogram
    macd = df["ema_12"] - df["ema_26"]
    signal = macd.ewm(span=9, adjust=False).mean()
    df["macd_hist"] = macd - signal

    # RSI
    d  = df["close"].diff()
    up = d.clip(lower=0).rolling(14).mean()
    dn = (-d.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"]  - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()

    return df


# ------------------------------------------------------------------
# build one symbol
# ------------------------------------------------------------------

def build_symbol(conn, symbol, verbose=True):
    if verbose:
        print(f"  [{symbol}]")

    # ---- 1h base
    h1 = load_ohlcv(conn, symbol, "1h")
    if h1.empty:
        if verbose: print("    no 1h data")
        return 0
    h1 = add_indicators(h1)
    if verbose: print(f"    1h bars    : {len(h1)}")

    # ---- 4h forward-filled
    h4 = load_ohlcv(conn, symbol, "4h")
    if not h4.empty:
        h4 = add_indicators(h4)
        h4 = h4[["rsi_14", "macd_hist", "sma_50"]].rename(columns={
            "rsi_14": "rsi_14_4h",
            "macd_hist": "macd_hist_4h",
            "sma_50": "sma_50_4h",
        })
        # forward-fill: each 1h bar gets the latest 4h value
        h4 = h4.reindex(h1.index, method="ffill")
    else:
        h4 = pd.DataFrame(index=h1.index,
                          columns=["rsi_14_4h", "macd_hist_4h", "sma_50_4h"])

    # ---- 1d forward-filled
    d1 = load_ohlcv(conn, symbol, "1d")
    if not d1.empty:
        d1 = add_indicators(d1)
        d1 = d1[["rsi_14", "sma_50", "sma_200"]].rename(columns={
            "rsi_14": "rsi_14_1d",
            "sma_50": "sma_50_1d",
            "sma_200": "sma_200_1d",
        })
        d1 = d1.reindex(h1.index, method="ffill")
    else:
        d1 = pd.DataFrame(index=h1.index,
                          columns=["rsi_14_1d", "sma_50_1d", "sma_200_1d"])

    # ---- join everything
    df = h1.copy()
    df = df.join(h4, how="left")
    df = df.join(d1, how="left")

    # ---- futures
    funding = load_funding(conn, symbol)
    if not funding.empty:
        funding["funding_3d_avg"] = funding["rate"].rolling(9).mean()  # 3d of 8h
        f = funding.reindex(h1.index, method="ffill")
        df["funding"] = f["rate"]
        df["funding_3d_avg"] = f["funding_3d_avg"]
    else:
        df["funding"] = np.nan
        df["funding_3d_avg"] = np.nan

    oi = load_oi(conn, symbol)
    if not oi.empty:
        oi_ff = oi.reindex(h1.index, method="ffill")
        df["oi"] = oi_ff["oi"]
        df["oi_chg_24h"] = oi_ff["oi"].pct_change(24)
    else:
        df["oi"] = np.nan
        df["oi_chg_24h"] = np.nan

    ls = load_ls(conn, symbol)
    if not ls.empty:
        ls["ls_ratio_7d_avg"] = ls["ratio"].rolling(24 * 7).mean()
        l = ls.reindex(h1.index, method="ffill")
        df["ls_ratio"] = l["ratio"]
        df["ls_ratio_7d_avg"] = l["ls_ratio_7d_avg"]
    else:
        df["ls_ratio"] = np.nan
        df["ls_ratio_7d_avg"] = np.nan

    taker = load_taker(conn, symbol)
    if not taker.empty:
        t = taker.reindex(h1.index, method="ffill")
        df["taker_ratio"] = t["buy_ratio"]
    else:
        df["taker_ratio"] = np.nan

    # ---- regime
    df["trend_up"]   = ((df["close"] > df["sma_50"]) &
                        (df["sma_50"] > df["sma_200"])).astype(int)
    df["trend_down"] = ((df["close"] < df["sma_50"]) &
                        (df["sma_50"] < df["sma_200"])).astype(int)

    def regime(row):
        if row["trend_up"] == 1:   return "bull"
        if row["trend_down"] == 1: return "bear"
        return "chop"
    df["regime"] = df.apply(regime, axis=1)

    # vol regime (percentile of vol_20)
    if df["vol_20"].notna().any():
        pct = df["vol_20"].rank(pct=True)
        df["vol_regime"] = np.where(pct > 0.8, "high",
                            np.where(pct < 0.2, "low", "normal"))
    else:
        df["vol_regime"] = "normal"

    # ---- distances
    df["dist_sma50"]    = (df["close"] - df["sma_50"])  / df["sma_50"]
    df["dist_sma200"]   = (df["close"] - df["sma_200"]) / df["sma_200"]
    df["dist_sma50_1d"] = (df["close"] - df["sma_50_1d"]) / df["sma_50_1d"]

    # ---- calendar
    df["hour"]    = df.index.hour
    df["weekday"] = df.index.dayofweek

    # ---- targets (forward-looking, for backtest only)
    df["target_1h"]  = df["close"].pct_change(1).shift(-1)
    df["target_4h"]  = df["close"].pct_change(4).shift(-4)
    df["target_24h"] = df["close"].pct_change(24).shift(-24)

    df["dir_1h"]  = np.where(df["target_1h"] > 0, 1, -1)
    df["dir_4h"]  = np.where(df["target_4h"] > 0, 1, -1)
    df["dir_24h"] = np.where(df["target_24h"] > 0, 1, -1)

    # ---- write
    keep_cols = [
        "open", "high", "low", "close", "volume",
        "ret_1", "ret_5", "ret_20", "vol_20",
        "rsi_14", "macd_hist", "atr_14", "sma_20", "sma_50", "sma_200",
        "ema_12", "ema_26",
        "rsi_14_4h", "macd_hist_4h", "sma_50_4h",
        "rsi_14_1d", "sma_50_1d", "sma_200_1d",
        "funding", "funding_3d_avg",
        "oi", "oi_chg_24h",
        "ls_ratio", "ls_ratio_7d_avg",
        "taker_ratio",
        "regime", "vol_regime", "trend_up", "trend_down",
        "dist_sma50", "dist_sma200", "dist_sma50_1d",
        "hour", "weekday",
        "target_1h", "target_4h", "target_24h",
        "dir_1h", "dir_4h", "dir_24h",
    ]
    out = df[keep_cols].copy()
    out.insert(0, "ts", (out.index.astype("int64") // 10**6))
    out.insert(0, "symbol", symbol)
    out = out.reset_index(drop=True)

    # drop first 200 rows (SMA200 not ready) and last 24 rows (targets NaN)
    out = out.iloc[200:-24]
    if len(out) == 0:
        if verbose: print("    not enough data")
        return 0

    out.to_sql("features", conn, if_exists="append", index=False)
    conn.commit()

    if verbose:
        print(f"    wrote     : {len(out)} rows")
        print(f"    range     : {out['ts'].min()} -> {out['ts'].max()}")
    return len(out)


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    ap.add_argument("--full", action="store_true",
                    help="drop the features table first (clean rebuild)")
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    try:
        # check table exists
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='features'"
        ).fetchone()
        if not exists:
            print("features table not found — run: python database/init_db.py")
            return 1

        if args.full:
            print("  dropping features table (--full)")
            conn.execute("DELETE FROM features")
            conn.commit()
        else:
            # incremental: delete rows for these symbols
            for sym in symbols:
                conn.execute("DELETE FROM features WHERE symbol=?", (sym,))
            conn.commit()

        print("=" * 60)
        print("  BUILD FEATURES")
        print("=" * 60)
        print(f"  symbols: {', '.join(symbols)}")
        print()

        t0 = time.time()
        total = 0
        for sym in symbols:
            try:
                n = build_symbol(conn, sym)
                total += n
            except Exception as e:
                print(f"  {sym} FAIL: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

        elapsed = time.time() - t0
        print()
        print("=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(f"  rows written : {total}")
        print(f"  time         : {elapsed:.1f}s")

        # per-symbol counts
        rows = conn.execute(
            "SELECT symbol, COUNT(*) FROM features GROUP BY symbol ORDER BY symbol"
        ).fetchall()
        print()
        print("  features table:")
        for sym, n in rows:
            print(f"    {sym:<10} {n:>7}")

        # regime breakdown
        print()
        print("  regime breakdown (all symbols):")
        rows = conn.execute(
            "SELECT regime, COUNT(*) FROM features GROUP BY regime ORDER BY regime"
        ).fetchall()
        for r, n in rows:
            print(f"    {r:<10} {n:>7}")

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
