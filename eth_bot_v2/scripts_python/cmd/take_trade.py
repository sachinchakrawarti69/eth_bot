"""Take-Trade - terminal version with live prices.

Run:
    python -m scripts_python.cmd.take_trade
    python -m scripts_python.cmd.take_trade --loop      # refresh every 30s
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


ROOT   = Path(__file__).resolve().parents[2]
MKT_DB = ROOT / "database" / "market.db"
OPT_DB = ROOT / "database" / "options.db"

PRICE_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]


# ------------------------------------------------------------------
# data
# ------------------------------------------------------------------

def sql(db, q, *p):
    with sqlite3.connect(db) as c:
        return pd.read_sql_query(q, c, params=p if p else None)


def load_ohlcv(symbol, timeframe="1d", limit=400):
    df = sql(
        MKT_DB,
        "SELECT open_time, open, high, low, close, volume "
        "FROM ohlcv WHERE symbol=? AND timeframe=? "
        "ORDER BY open_time DESC LIMIT ?",
        symbol, timeframe, limit)
    if df.empty:
        return df
    df = df.sort_values("open_time").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.drop(columns=["open_time"]).set_index("date")
    df["return"] = df["close"].pct_change()
    df["sma_20"]  = df["close"].rolling(20).mean()
    df["sma_50"]  = df["close"].rolling(50).mean()
    df["sma_200"] = df["close"].rolling(200).mean()
    d  = df["close"].diff()
    up = d.clip(lower=0).rolling(14).mean()
    dn = (-d.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    tr = pd.concat([
        df.high - df.low,
        (df.high - df.close.shift()).abs(),
        (df.low  - df.close.shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    df["vol_20"] = df["return"].rolling(20).std()
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    df["macd_hist"] = macd - macd.ewm(span=9, adjust=False).mean()
    return df


def get_prices():
    """Live prices from Binance API (falls back to DB)."""
    return get_live_prices()


# ------------------------------------------------------------------
# live prices (Binance ticker)
# ------------------------------------------------------------------

_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
_TICKER_CACHE = {"time": 0, "data": {}}
_TICKER_TTL = 10  # seconds


def get_live_prices(symbols=None):
    """Fetch live prices from Binance ticker. Cached for 10 seconds."""
    import time, json
    import urllib.request

    if symbols is None:
        symbols = PRICE_SYMBOLS

    now = time.time()
    if now - _TICKER_CACHE["time"] < _TICKER_TTL and _TICKER_CACHE["data"]:
        cache = _TICKER_CACHE["data"]
        if all(s in cache for s in symbols):
            return {s: cache[s] for s in symbols}

    out = {}
    for sym in symbols:
        try:
            url = f"{_TICKER_URL}?symbol={sym}"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode("utf-8"))
            out[sym] = {
                "price":  float(data["lastPrice"]),
                "change": float(data["priceChangePercent"]),
                "change_abs": float(data["priceChange"]),
                "high":   float(data["highPrice"]),
                "low":    float(data["lowPrice"]),
                "volume": float(data["volume"]),
            }
        except Exception as e:
            # fall back to DB close if API fails
            try:
                df = sql(MKT_DB,
                    "SELECT close FROM ohlcv WHERE symbol=? AND timeframe='1d' "
                    "ORDER BY open_time DESC LIMIT 2",
                    sym)
                if len(df) >= 2:
                    latest = float(df.close.iloc[0])
                    prev   = float(df.close.iloc[1])
                    out[sym] = {
                        "price": latest,
                        "change": (latest/prev - 1) * 100,
                        "change_abs": latest - prev,
                        "high": None, "low": None, "volume": None,
                        "stale": True,
                    }
            except Exception:
                pass

    _TICKER_CACHE["time"] = now
    _TICKER_CACHE["data"].update(out)
    return out


def load_last_funding(symbol="ETHUSDT"):
    try:
        df = sql(MKT_DB,
            "SELECT rate FROM funding_rate WHERE symbol=? ORDER BY ts DESC LIMIT 1",
            symbol)
        if df.empty:
            return None
        v = df.rate.iloc[0]
        return None if pd.isna(v) else float(v)
    except Exception:
        return None


def load_oi_change(symbol="ETHUSDT", lookback=8):
    try:
        df = sql(MKT_DB,
            "SELECT oi FROM open_interest WHERE symbol=? ORDER BY ts DESC LIMIT ?",
            symbol, lookback)
        if len(df) < 2:
            return None
        v = (df.oi.iloc[0] / df.oi.iloc[-1] - 1) * 100
        return None if pd.isna(v) else float(v)
    except Exception:
        return None


def load_fear_greed():
    try:
        df = sql(MKT_DB, "SELECT value FROM fear_greed ORDER BY ts DESC LIMIT 1")
        if df.empty:
            return None
        v = df.value.iloc[0]
        return None if pd.isna(v) else int(v)
    except Exception:
        return None


def load_option_summary(underlying="ETH"):
    try:
        df = sql(OPT_DB,
            "SELECT * FROM option_summary WHERE underlying=? ORDER BY ts DESC LIMIT 1",
            underlying)
        return df.iloc[0] if not df.empty else None
    except Exception:
        return None


def safe_num(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    try:
        return float(v)
    except Exception:
        return None


# ------------------------------------------------------------------
# score
# ------------------------------------------------------------------

def score_opportunity():
    eth = load_ohlcv("ETHUSDT")
    btc = load_ohlcv("BTCUSDT")
    if eth.empty:
        return None

    last = eth.iloc[-1]
    price = float(last.close)
    # use live price if available
    try:
        _live = get_live_prices(["ETHUSDT"])
        if "ETHUSDT" in _live and _live["ETHUSDT"].get("price"):
            price = float(_live["ETHUSDT"]["price"])
    except Exception:
        pass
    sma50  = safe_num(last.sma_50)
    sma200 = safe_num(last.sma_200)
    rsi    = safe_num(last.rsi_14)
    atr    = safe_num(last.atr_14)
    macd_h = safe_num(last.macd_hist)

    btc_up = False
    if not btc.empty:
        bl = btc.iloc[-1]
        if pd.notna(bl.sma_50):
            btc_up = bool(bl.close > bl.sma_50)

    corr = None
    if not btc.empty and not eth.empty:
        b = btc["close"].pct_change()
        e = eth["close"].pct_change()
        m = pd.concat([b, e], axis=1).dropna().tail(30)
        if len(m) > 5:
            cv = m.corr().iloc[0, 1]
            corr = None if pd.isna(cv) else float(cv)

    fund = load_last_funding("ETHUSDT")
    fg   = load_fear_greed()
    opt  = load_option_summary("ETH")

    pcr      = safe_num(opt["pcr_oi"])   if opt is not None else None
    atm_iv   = safe_num(opt["atm_iv"])   if opt is not None else None
    max_pain = safe_num(opt["max_pain"]) if opt is not None else None

    bull, bear = 0, 0
    why_bull, why_bear = [], []

    if sma50 and sma200:
        if price > sma50 > sma200:
            bull += 2; why_bull.append("strong uptrend")
        elif price > sma50:
            bull += 1; why_bull.append("above SMA50")
        elif price < sma50 < sma200:
            bear += 2; why_bear.append("strong downtrend")
        else:
            bear += 1; why_bear.append("below SMA50")

    if btc_up:
        bull += 1; why_bull.append("BTC up")
    else:
        bear += 1; why_bear.append("BTC down")

    if macd_h is not None:
        if macd_h > 0:
            bull += 1; why_bull.append("MACD positive")
        else:
            bear += 1; why_bear.append("MACD negative")

    if rsi is not None:
        if rsi < 30:
            bull += 1; why_bull.append("RSI oversold")
        elif rsi > 70:
            bear += 1; why_bear.append("RSI overbought")

    if fund is not None:
        if fund > 0.001:
            bear += 1; why_bear.append("crowded long (funding)")
        elif fund < -0.001:
            bull += 1; why_bull.append("crowded short (funding)")

    if fg is not None:
        if fg < 20:
            bull += 1; why_bull.append("extreme fear (F&G)")
        elif fg > 80:
            bear += 1; why_bear.append("extreme greed (F&G)")

    if pcr is not None:
        if pcr > 1.3:
            bull += 1; why_bull.append("PCR high (fear)")
        elif pcr < 0.7:
            bear += 1; why_bear.append("PCR low (greed)")

    if bull >= 4 and btc_up:
        action = "LONG"
        reason = " + ".join(why_bull[:3]) or "bullish"
    elif bear >= 4 and not btc_up:
        action = "SHORT"
        reason = " + ".join(why_bear[:3]) or "bearish"
    else:
        action = "FLAT"
        reason = "mixed signals"

    total = bull + bear
    score = 0 if total == 0 else int(round(abs(bull - bear) / max(total, 1) * 100))
    if action == "FLAT":
        score = min(score, 40)
    if btc_up and action == "LONG":
        score = min(100, score + 5)
    if not btc_up and action == "SHORT":
        score = min(100, score + 5)
    if corr is not None and corr > 0.85:
        score = max(0, score - 5)

    if score >= 85:   tier = "A+"
    elif score >= 70: tier = "A"
    elif score >= 55: tier = "B"
    elif score >= 40: tier = "C"
    else:             tier = "D"

    stop_dist = 1.5 * atr if atr else 0
    if action == "LONG":
        entry, stop, target = price, price - stop_dist, price + 2 * stop_dist
    elif action == "SHORT":
        entry, stop, target = price, price + stop_dist, price - 2 * stop_dist
    else:
        entry = stop = target = price

    rr = 0
    if action != "FLAT" and stop_dist:
        rr = abs(target - entry) / abs(entry - stop)

    if sma50 and sma200 and price > sma50 > sma200:
        trend = "strong up"
    elif sma50 and price > sma50:
        trend = "up"
    elif sma50 and sma200 and price < sma50 < sma200:
        trend = "strong down"
    else:
        trend = "down"

    return {
        "time":       datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "symbol":     "ETHUSDT",
        "price":      price,
        "action":     action,
        "score":      score,
        "tier":       tier,
        "reason":     reason,
        "bull":       bull,
        "bear":       bear,
        "why_bull":   why_bull,
        "why_bear":   why_bear,
        "entry":      entry,
        "stop":       stop,
        "target":     target,
        "rr":         rr,
        "atr":        atr,
        "expires":    (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M UTC"),
        "btc_up":     btc_up,
        "corr":       corr,
        "funding":    fund,
        "fear_greed": fg,
        "pcr":        pcr,
        "atm_iv":     atm_iv,
        "max_pain":   max_pain,
        "rsi":        rsi,
        "trend":      trend,
    }


# ------------------------------------------------------------------
# pretty print
# ------------------------------------------------------------------

GREEN  = "32"
RED    = "31"
YELLOW = "33"
CYAN   = "36"
GRAY   = "90"
BOLD   = "1"
WHITE  = "97"


def c(text, code):
    return f"\033[{code}m{text}\033[0m"


def bar(score, width=50):
    filled = int(round(score / 100 * width))
    return "#" * filled + "-" * (width - filled)


def price_color(change):
    return GREEN if change >= 0 else RED


def print_price_bar(prices):
    """Top row: BTC / ETH / SOL / BNB price + 24h change."""
    sep = "-" * 72
    print(c(sep, GRAY))
    header = "  PRICES  "
    print(c(header, GRAY))

    cells = []
    for sym in PRICE_SYMBOLS:
        if sym not in prices:
            cells.append(f"{sym:<10} --")
            continue
        p = prices[sym]
        name = sym.replace("USDT", "")
        chg = p["change"]
        sign = "+" if chg >= 0 else ""
        cell = f"{name:<5} {p['price']:>12,.2f}  {sign}{chg:>5.2f}%"
        cells.append(cell)

    # two per line
    for i in range(0, len(cells), 2):
        pair = cells[i:i+2]
        line = "   ".join(pair)
        # color each cell individually
        out = "  "
        for cell in pair:
            if "--" in cell:
                out += c(cell, GRAY) + "     "
            else:
                # extract change sign
                if "+" in cell.split()[-1]:
                    out += c(cell, GREEN) + "     "
                elif "-" in cell.split()[-1]:
                    out += c(cell, RED) + "     "
                else:
                    out += c(cell, WHITE) + "     "
        print(out)
    print(c(sep, GRAY))
    print()


def print_report(o, prices):
    if o is None:
        print(c("no data - run the fetch first", RED))
        return

    action = o["action"]
    if action == "LONG":
        action_color = GREEN
    elif action == "SHORT":
        action_color = RED
    else:
        action_color = GRAY

    sep = "=" * 72

    print()
    print(c(sep, CYAN))
    print(c("  TAKE TRADE - opportunity report", CYAN))
    print(c(sep, CYAN))
    print()

    # ---- price bar
    print_price_bar(prices)

    print(f"  {c('time', GRAY):<20} {o['time']}")
    print(f"  {c('symbol', GRAY):<20} {o['symbol']}")
    print(f"  {c('ETH price', GRAY):<20} {o['price']:,.2f}")
    print(f"  {c('trend', GRAY):<20} {o['trend']}")
    rsi_str = f"{o['rsi']:.1f}" if o['rsi'] is not None else "n/a"
    print(f"  {c('RSI(14)', GRAY):<20} {rsi_str}")
    print()

    # ---- ACTION banner
    print(c(sep, CYAN))
    print(f"  {c('CURRENT ACTION', GRAY)}")
    print(c(sep, CYAN))
    print(f"  {c(action.center(68), action_color + ';' + BOLD)}")
    print(c(sep, CYAN))
    print()

    print(f"  {c('SCORE', GRAY):<20} {bar(o['score'])}  {o['score']}/100  [{o['tier']}]")
    print(f"  {c('confidence', GRAY):<20} {o['score']/100:.2f}")
    print(f"  {c('votes', GRAY):<20} {o['bull']} bullish / {o['bear']} bearish")
    print(f"  {c('reason', GRAY):<20} {o['reason']}")
    print()

    if action != "FLAT":
        stop_pct   = abs(o['entry'] - o['stop']) / o['entry'] * 100
        target_pct = abs(o['target'] - o['entry']) / o['entry'] * 100
        print(c("  LEVELS", BOLD + ";" + WHITE))
        print(f"    {c('entry', GRAY):<12} {o['entry']:>12,.2f}")
        print(f"    {c('stop', GRAY):<12} {o['stop']:>12,.2f}   ({stop_pct:>5.2f}%)")
        print(f"    {c('target', GRAY):<12} {o['target']:>12,.2f}   ({target_pct:>5.2f}%)")
        print(f"    {c('R:R', GRAY):<12} {o['rr']:>12.2f} : 1")
        atr_str = f"{o['atr']:.2f}" if o['atr'] is not None else "n/a"
        print(f"    {c('ATR(14)', GRAY):<12} {atr_str:>12}")
        print(f"    {c('valid until', GRAY):<12} {o['expires']}")
    else:
        print(c("  NO TRADE SETUP", YELLOW))
        print(f"    reason: {o['reason']}")
    print()

    print(c("  WHY", BOLD + ";" + WHITE))
    if o["why_bull"]:
        print(f"    {c('bullish', GREEN)}:")
        for r in o["why_bull"]:
            print(f"      + {r}")
    if o["why_bear"]:
        print(f"    {c('bearish', RED)}:")
        for r in o["why_bear"]:
            print(f"      - {r}")
    if not o["why_bull"] and not o["why_bear"]:
        print(f"    {c('(no signals)', GRAY)}")
    print()

    print(c("  CONTEXT", BOLD + ";" + WHITE))
    print(f"    {c('BTC up', GRAY):<14} {o['btc_up']}")
    if o["corr"] is not None:
        print(f"    {c('BTC-ETH r', GRAY):<14} {o['corr']:.2f}")
    if o["funding"] is not None:
        print(f"    {c('funding 8h', GRAY):<14} {o['funding']*100:+.4f}%")
    if o["fear_greed"] is not None:
        print(f"    {c('fear&greed', GRAY):<14} {o['fear_greed']}")
    if o["pcr"] is not None:
        print(f"    {c('PCR (OI)', GRAY):<14} {o['pcr']:.3f}")
    if o["atm_iv"] is not None:
        print(f"    {c('ATM IV', GRAY):<14} {o['atm_iv']*100:.1f}%")
    if o["max_pain"] is not None:
        print(f"    {c('max pain', GRAY):<14} {o['max_pain']:.0f}")
    print()

    print(c(sep, CYAN))
    if action == "FLAT":
        line = f"FLAT  |  {o['reason']}  |  score {o['score']}"
    else:
        line = (f"{action}  |  entry {o['entry']:.2f}  "
                f"stop {o['stop']:.2f}  target {o['target']:.2f}  "
                f"|  score {o['score']}  tier {o['tier']}")
    print(f"  {c(line, action_color + ';' + BOLD)}")
    print(c(sep, CYAN))
    print()


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def clear_screen():
    if sys.platform == "win32":
        import os
        os.system("cls")
    else:
        print("\033[2J\033[H", end="")


def run_once(gui=False):
    try:
        prices = get_prices()
        o = score_opportunity()
    except Exception:
        import traceback
        traceback.print_exc()
        return 1

    print_report(o, prices)

    if gui:
        try:
            from scripts_python.gui.take_trade import main as gui_main
            gui_main()
        except Exception:
            import traceback
            traceback.print_exc()
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true", help="refresh every 30s")
    ap.add_argument("--interval", type=int, default=30, help="seconds between refreshes")
    ap.add_argument("--gui", action="store_true", help="open GUI after the report")
    args = ap.parse_args()

    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass

    if args.loop:
        try:
            while True:
                clear_screen()
                run_once(gui=False)
                print(c(f"  refreshing in {args.interval}s   (Ctrl+C to stop)", GRAY))
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print()
            print(c("  stopped.", GRAY))
            return 0

    run_once(gui=args.gui)

    if not args.gui:
        print()
        try:
            ans = input("open GUI? [y/N]: ").strip().lower()
        except EOFError:
            ans = "n"
        if ans == "y":
            run_once(gui=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())