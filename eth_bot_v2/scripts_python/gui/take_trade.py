"""Take-Trade GUI - opportunity finder.

Run:
    python -m scripts_python.gui.take_trade

Shows a single OPPORTUNITY verdict with score, tier, direction, levels.
"""

from __future__ import annotations

import sqlite3
import tkinter as tk
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tkinter import ttk

import numpy as np
import pandas as pd


ROOT   = Path(__file__).resolve().parents[2]
MKT_DB = ROOT / "database" / "market.db"
OPT_DB = ROOT / "database" / "options.db"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]


# ------------------------------------------------------------------
# data
# ------------------------------------------------------------------

def sql(db, q, **p):
    with sqlite3.connect(db) as c:
        return pd.read_sql_query(q, c, params=p)


def load_ohlcv(symbol, timeframe="1d", limit=400):
    df = sql(MKT_DB,
        "SELECT open_time, open, high, low, close, volume "
        "FROM ohlcv WHERE symbol=? AND timeframe=? "
        "ORDER BY open_time DESC LIMIT ?",
        **{"1": symbol, "2": timeframe, "3": limit})
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
    tr = pd.concat([df.high - df.low,
                    (df.high - df.close.shift()).abs(),
                    (df.low  - df.close.shift()).abs()], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    df["vol_20"] = df["return"].rolling(20).std()
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    df["macd_hist"] = macd - macd.ewm(span=9, adjust=False).mean()
    return df


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
            **{"1": symbol})
        return float(df.rate.iloc[0]) if not df.empty else None
    except Exception:
        return None


def load_oi_change(symbol="ETHUSDT", lookback=8):
    try:
        df = sql(MKT_DB,
            "SELECT oi FROM open_interest WHERE symbol=? ORDER BY ts DESC LIMIT ?",
            **{"1": symbol, "2": lookback})
        if len(df) < 2:
            return None
        return float((df.oi.iloc[0] / df.oi.iloc[-1] - 1) * 100)
    except Exception:
        return None


def load_fear_greed():
    try:
        df = sql(MKT_DB, "SELECT value FROM fear_greed ORDER BY ts DESC LIMIT 1")
        return int(df.value.iloc[0]) if not df.empty else None
    except Exception:
        return None


def load_option_summary(underlying="ETH"):
    try:
        df = sql(OPT_DB,
            "SELECT * FROM option_summary WHERE underlying=? ORDER BY ts DESC LIMIT 1",
            **{"1": underlying})
        return df.iloc[0] if not df.empty else None
    except Exception:
        return None


def safe(row, key):
    try:
        v = row[key]
        return None if pd.isna(v) else v
    except Exception:
        return None


# ------------------------------------------------------------------
# opportunity scoring
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
    sma50 = float(last.sma_50) if pd.notna(last.sma_50) else None
    sma200 = float(last.sma_200) if pd.notna(last.sma_200) else None
    rsi = float(last.rsi_14) if pd.notna(last.rsi_14) else None
    atr = float(last.atr_14) if pd.notna(last.atr_14) else None
    macd_h = float(last.macd_hist) if pd.notna(last.macd_hist) else None

    h52 = float(eth["high"].tail(365).max())
    l52 = float(eth["low"].tail(365).min())
    pos52 = (price - l52) / (h52 - l52) if h52 > l52 else None

    btc_last = btc.iloc[-1] if not btc.empty else None
    btc_up = (btc_last is not None
              and pd.notna(btc_last.sma_50)
              and btc_last.close > btc_last.sma_50)

    # correlation
    corr = None
    if not btc.empty and not eth.empty:
        b = btc["close"].pct_change()
        e = eth["close"].pct_change()
        m = pd.concat([b, e], axis=1).dropna().tail(30)
        if len(m) > 5:
            corr = float(m.corr().iloc[0, 1])

    fund = load_last_funding("ETHUSDT")
    oi_chg = load_oi_change("ETHUSDT", 8)
    fg = load_fear_greed()
    opt = load_option_summary("ETH")
    pcr = safe(opt, "pcr_oi") if opt is not None else None
    atm_iv = safe(opt, "atm_iv") if opt is not None else None
    max_pain = safe(opt, "max_pain") if opt is not None else None

    # ---- votes
    bull = 0
    bear = 0
    reasons_bull = []
    reasons_bear = []

    # trend
    if sma50 and sma200:
        if price > sma50 > sma200:
            bull += 2; reasons_bull.append("strong uptrend")
        elif price > sma50:
            bull += 1; reasons_bull.append("above SMA50")
        elif price < sma50 < sma200:
            bear += 2; reasons_bear.append("strong downtrend")
        else:
            bear += 1; reasons_bear.append("below SMA50")

    # BTC
    if btc_up:
        bull += 1; reasons_bull.append("BTC up")
    else:
        bear += 1; reasons_bear.append("BTC down")

    # MACD
    if macd_h is not None:
        if macd_h > 0:
            bull += 1; reasons_bull.append("MACD positive")
        else:
            bear += 1; reasons_bear.append("MACD negative")

    # RSI
    if rsi is not None:
        if rsi < 30:
            bull += 1; reasons_bull.append("RSI oversold")
        elif rsi > 70:
            bear += 1; reasons_bear.append("RSI overbought")

    # funding (contrarian)
    if fund is not None:
        if fund > 0.001:
            bear += 1; reasons_bear.append("crowded long (funding)")
        elif fund < -0.001:
            bull += 1; reasons_bull.append("crowded short (funding)")

    # fear & greed (contrarian)
    if fg is not None:
        if fg < 20:
            bull += 1; reasons_bull.append("extreme fear (F&G)")
        elif fg > 80:
            bear += 1; reasons_bear.append("extreme greed (F&G)")

    # options
    if pcr is not None and pcr > 1.3:
        bull += 1; reasons_bull.append("PCR high (fear)")
    if pcr is not None and pcr < 0.7:
        bear += 1; reasons_bear.append("PCR low (greed)")

    # ---- direction
    if bull >= 4 and btc_up:
        action = "LONG"
        reason = " + ".join(reasons_bull[:3]) or "multiple bullish signals"
    elif bear >= 4 and not btc_up:
        action = "SHORT"
        reason = " + ".join(reasons_bear[:3]) or "multiple bearish signals"
    else:
        action = "FLAT"
        reason = "mixed signals"

    # ---- score (0-100)
    total = bull + bear
    if total == 0:
        score = 0
    else:
        score = int(round((abs(bull - bear) / max(total, 1)) * 100))

    # cap by action
    if action == "FLAT":
        score = min(score, 40)

    # small bonuses for context quality
    if btc_up and action == "LONG": score = min(100, score + 5)
    if not btc_up and action == "SHORT": score = min(100, score + 5)
    if corr is not None and corr > 0.85: score = max(0, score - 5)  # less diversification

    # tier
    if score >= 85:   tier = "A+"
    elif score >= 70: tier = "A"
    elif score >= 55: tier = "B"
    elif score >= 40: tier = "C"
    else:             tier = "D"

    # ---- levels
    stop_dist = 1.5 * atr if atr else 0
    if action == "LONG":
        entry, stop, target = price, price - stop_dist, price + 2 * stop_dist
    elif action == "SHORT":
        entry, stop, target = price, price + stop_dist, price - 2 * stop_dist
    else:
        entry = stop = target = price

    rr = (abs(target - entry) / max(abs(entry - stop), 1e-9)) if action != "FLAT" else 0

    # confidence 0-1
    conf = score / 100

    # expiry window
    expiry = (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "time":     datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "symbol":   "ETHUSDT",
        "price":    price,
        "action":   action,
        "score":    score,
        "tier":     tier,
        "confidence": conf,
        "reason":   reason,
        "bull":     bull,
        "bear":     bear,
        "bull_reasons": reasons_bull,
        "bear_reasons": reasons_bear,
        "entry":    entry,
        "stop":     stop,
        "target":   target,
        "rr":       rr,
        "atr":      atr,
        "expires":  expiry,
        "btc_up":   btc_up,
        "corr":     corr,
        "funding":  fund,
        "fear_greed": fg,
        "pcr":      pcr,
        "atm_iv":   atm_iv,
        "max_pain": max_pain,
        "rsi":      rsi,
        "trend":    ("strong up" if sma50 and sma200 and price > sma50 > sma200 else
                     "up" if sma50 and price > sma50 else
                     "strong down" if sma50 and sma200 and price < sma50 < sma200 else
                     "down"),
    }


# ------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------

TIER_COLORS = {
    "A+": "#5ec95e",
    "A":  "#7ec87e",
    "B":  "#d8b450",
    "C":  "#c87e50",
    "D":  "#e06060",
}

ACTION_COLORS = {
    "LONG":  "#7ec87e",
    "SHORT": "#e06060",
    "FLAT":  "#a0a0a0",
}


class OpportunityApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Take Trade - Opportunity")
        root.geometry("860x800")
        root.configure(bg="#1e1e1e")
        root.minsize(720, 640)

        # ---- header
        header = tk.Frame(root, bg="#1e1e1e")
        header.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(header, text="TAKE TRADE",
                 font=("Consolas", 20, "bold"),
                 fg="#e0e0e0", bg="#1e1e1e").pack(side="left")
        tk.Label(header, text="opportunity scanner",
                 font=("Consolas", 11),
                 fg="#808080", bg="#1e1e1e").pack(side="left", padx=(10, 0))

        # ---- action bar (BIG verdict)
        self.action_frame = tk.Frame(root, bg="#101010",
                                     highlightthickness=2,
                                     highlightbackground="#303030")
        self.action_frame.pack(fill="x", padx=16, pady=8)

        self.action_label = tk.Label(self.action_frame,
                                     text="scanning...",
                                     font=("Consolas", 26, "bold"),
                                     fg="#808080", bg="#101010",
                                     pady=20)
        self.action_label.pack(fill="x")

        # ---- score bar
        self.score_frame = tk.Frame(root, bg="#1e1e1e")
        self.score_frame.pack(fill="x", padx=16, pady=4)

        self.score_canvas = tk.Canvas(self.score_frame, height=32,
                                      bg="#101010", highlightthickness=1,
                                      highlightbackground="#303030")
        self.score_canvas.pack(fill="x", pady=(0, 4))

        self.score_text = tk.Label(self.score_frame, text="score: -",
                                   fg="#a0a0a0", bg="#1e1e1e",
                                   font=("Consolas", 11))
        self.score_text.pack(anchor="w")

        # ---- main body (two columns)
        body = tk.Frame(root, bg="#1e1e1e")
        body.pack(fill="both", expand=True, padx=16, pady=6)

        # left: levels + reason
        left = tk.Frame(body, bg="#1e1e1e")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.levels_frame = tk.LabelFrame(left, text=" LEVELS ",
                                          fg="#a0a0a0", bg="#1e1e1e",
                                          font=("Consolas", 11, "bold"),
                                          bd=1, relief="solid",
                                          labelanchor="nw")
        self.levels_frame.pack(fill="x", pady=(0, 8))
        self.levels_label = tk.Label(self.levels_frame, text="-",
                                     fg="#e0e0e0", bg="#1e1e1e",
                                     font=("Consolas", 12),
                                     justify="left", anchor="w",
                                     padx=14, pady=10)
        self.levels_label.pack(fill="x")

        self.reason_frame = tk.LabelFrame(left, text=" WHY ",
                                          fg="#a0a0a0", bg="#1e1e1e",
                                          font=("Consolas", 11, "bold"),
                                          bd=1, relief="solid",
                                          labelanchor="nw")
        self.reason_frame.pack(fill="both", expand=True)
        self.reason_label = tk.Label(self.reason_frame, text="-",
                                     fg="#e0e0e0", bg="#1e1e1e",
                                     font=("Consolas", 11),
                                     justify="left", anchor="nw",
                                     padx=14, pady=10, wraplength=380)
        self.reason_label.pack(fill="both", expand=True)

        # right: context
        right = tk.Frame(body, bg="#1e1e1e")
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self.context_frame = tk.LabelFrame(right, text=" CONTEXT ",
                                           fg="#a0a0a0", bg="#1e1e1e",
                                           font=("Consolas", 11, "bold"),
                                           bd=1, relief="solid",
                                           labelanchor="nw")
        self.context_frame.pack(fill="both", expand=True)
        self.context_label = tk.Label(self.context_frame, text="-",
                                      fg="#e0e0e0", bg="#1e1e1e",
                                      font=("Consolas", 11),
                                      justify="left", anchor="nw",
                                      padx=14, pady=10)
        self.context_label.pack(fill="both", expand=True)

        # ---- refresh button + status
        bottom = tk.Frame(root, bg="#1e1e1e")
        bottom.pack(fill="x", padx=16, pady=(4, 14))

        self.refresh_btn = tk.Button(
            bottom, text="RESCAN", command=self.refresh,
            bg="#2d7c2d", fg="white", activebackground="#3d9c3d",
            font=("Consolas", 12, "bold"), relief="flat",
            padx=24, pady=8, cursor="hand2")
        self.refresh_btn.pack(side="left")

        self.status = tk.Label(bottom, text="ready",
                               fg="#a0a0a0", bg="#1e1e1e",
                               font=("Consolas", 10))
        self.status.pack(side="right")

        # auto-run
        root.after(150, self.refresh)

    # ---- refresh
    def refresh(self):
        self.status.config(text="scanning...", fg="#a0a0a0")
        self.root.update_idletasks()

        try:
            o = score_opportunity()
        except Exception as e:
            self.status.config(text=f"ERROR: {e}", fg="#e06060")
            return

        if o is None:
            self.status.config(text="no data", fg="#e06060")
            return

        # --- big action
        color = ACTION_COLORS.get(o["action"], "#a0a0a0")
        action_text = f"{o['action']}"
        self.action_label.config(text=action_text, fg=color)

        # --- score bar
        self._draw_score(o["score"], o["tier"])
        self.score_text.config(
            text=f"score {o['score']}/100    tier {o['tier']}    "
                 f"confidence {o['confidence']:.2f}    "
                 f"bullish {o['bull']} / bearish {o['bear']}")

        # --- levels
        if o["action"] == "FLAT":
            levels = ("No trade setup.\n\n"
                      "Wait for a clearer signal.")
        else:
            entry = o["entry"]
            stop  = o["stop"]
            target = o["target"]
            stop_pct  = abs(entry - stop) / entry * 100
            target_pct = abs(target - entry) / entry * 100
            levels = (
                f"  entry    {entry:>10,.2f}\n"
                f"  stop     {stop:>10,.2f}   ({stop_pct:>5.2f}%)\n"
                f"  target   {target:>10,.2f}   ({target_pct:>5.2f}%)\n"
                f"  R:R      {o['rr']:>10.2f} : 1\n"
                f"  ATR(14)  {o['atr']:>10,.2f}\n"
                f"\n"
                f"  valid until {o['expires']}"
            )
        self.levels_label.config(text=levels)

        # --- why
        bull_lines = "\n".join(f"  + {r}" for r in o["bull_reasons"]) or "  (none)"
        bear_lines = "\n".join(f"  - {r}" for r in o["bear_reasons"]) or "  (none)"
        why = (f"REASON: {o['reason']}\n\n"
               f"BULLISH:\n{bull_lines}\n\n"
               f"BEARISH:\n{bear_lines}")
        self.reason_label.config(text=why)

        # --- context
        ctx_lines = [
            f"  time        {o['time']}",
            f"  symbol      {o['symbol']}",
            f"  price       {o['price']:,.2f}",
            f"  trend       {o['trend']}",
            f"  RSI(14)     {o['rsi']:.1f}" if o['rsi'] is not None else "  RSI(14)     n/a",
            "",
            f"  BTC up      {o['btc_up']}",
            f"  BTC-ETH r   {o['corr']:.2f}" if o['corr'] is not None else "  BTC-ETH r   n/a",
            f"  funding     {o['funding']*100:+.4f}%" if o['funding'] is not None else "  funding     n/a",
            f"  fear&greed  {o['fear_greed']}" if o['fear_greed'] is not None else "  fear&greed  n/a",
            f"  PCR (OI)    {o['pcr']:.3f}" if o['pcr'] is not None else "  PCR (OI)    n/a",
            f"  ATM IV      {o['atm_iv']*100:.1f}%" if o['atm_iv'] is not None else "  ATM IV      n/a",
            f"  max pain    {o['max_pain']:.0f}" if o['max_pain'] is not None else "  max pain    n/a",
        ]
        self.context_label.config(text="\n".join(ctx_lines))

        # --- status
        self.status.config(
            text=f"{o['action']}  ·  tier {o['tier']}  ·  score {o['score']}",
            fg=color)

    def _draw_score(self, score, tier):
        c = self.score_canvas
        c.delete("all")
        w = c.winfo_width() or 800
        h = int(c["height"])
        # background
        c.create_rectangle(0, 0, w, h, fill="#101010", outline="")
        # fill
        fill_w = int(w * score / 100)
        color = TIER_COLORS.get(tier, "#7ec87e")
        c.create_rectangle(0, 0, fill_w, h, fill=color, outline="")
        # text
        c.create_text(w // 2, h // 2,
                      text=f"{score} / 100   [{tier}]",
                      fill="#000000" if score > 40 else "#e0e0e0",
                      font=("Consolas", 12, "bold"))


def main():
    root = tk.Tk()
    app = OpportunityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()