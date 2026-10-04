"""Write analysis/eth_current_prediction/*.ipynb - 13 specialized notebooks."""
import json
from pathlib import Path

DIR = Path(__file__).resolve().parent / "analysis" / "eth_current_prediction"

def md(t):   return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}
def code(s): return {"cell_type": "code", "execution_count": None, "metadata": {},
                     "outputs": [], "source": s.splitlines(keepends=True)}

SETUP = '''# --- setup --------------------------------------------------------
import sys, json
sys.path.insert(0, r"D:\\\\Projects\\\\done\\\\eth_bot\\\\eth_bot_v2")
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

pd.set_option("display.width", 180)
pd.set_option("display.max_columns", 60)
plt.rcParams["figure.figsize"] = (13, 4)
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3
np.random.seed(42)

SYMBOL = "ETHUSDT"
OUT = Path(r"D:\\\\Projects\\\\done\\\\eth_bot\\\\eth_bot_v2") / "reports" / "forecasts"
OUT.mkdir(parents=True, exist_ok=True)
DB = Path(r"D:\\\\Projects\\\\done\\\\eth_bot\\\\eth_bot_v2") / "database" / "market.db"

def sql(q, **p):
    with sqlite3.connect(DB) as c:
        return pd.read_sql_query(q, c, params=p)

from database.config.api.binance import get_klines

def fetch(symbol, interval, limit=500):
    raw = get_klines(symbol, interval=interval, limit=limit)
    df = pd.DataFrame(raw, columns=["open_time","open","high","low","close",
        "volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"])
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    for c in ("open","high","low","close","volume"):
        df[c] = df[c].astype(float)
    return df[["date","open","high","low","close","volume"]].set_index("date").iloc[:-1]

def action_block(name, action, reason, price=None, entry=None, stop=None,
                 target=None, conf=None, extra=None):
    print("=" * 62)
    print(f"  {name}")
    print("=" * 62)
    print(f"  time   : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    if price is not None: print(f"  price  : {price:,.2f}")
    if conf  is not None: print(f"  conf   : {conf:.2f}")
    print(f"  ACTION : {action}")
    print(f"  REASON : {reason}")
    if entry is not None:
        print(f"  entry  : {entry:,.2f}   stop: {stop:,.2f}   target: {target:,.2f}")
    if extra:
        for k, v in extra.items():
            print(f"  {k:<6} : {v}")
    print("=" * 62)
    return {"action": action, "reason": reason, "price": price,
            "entry": entry, "stop": stop, "target": target, "conf": conf}'''


def save(name, cells):
    p = DIR / name
    p.write_text(json.dumps({
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }, indent=1), encoding="utf-8")
    print("wrote", name)


def make_nb(title, intro, mid_sections, action_title, action_code):
    """Build a notebook: title + setup + mid_sections + action."""
    cells = [md(f"# {title}\n\n{intro}\n"), md("## Setup"), code(SETUP)]
    for m_title, m_text, c_code in mid_sections:
        cells.append(md(f"## {m_title}\n\n{m_text}\n"))
        cells.append(code(c_code))
    cells.append(md(f"## {action_title}"))
    cells.append(code(action_code))
    return cells


# ================================================================
# 01 dashboard
# ================================================================
save("01_dashboard.ipynb", [
    md("# 01 - Dashboard\n\nAll factors into one action.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Fetch ETH 1h and 1d"),
    code('''eth_1h = fetch("ETHUSDT", "1h", 500)
eth_1d = fetch("ETHUSDT", "1d", 500)
print("1h:", len(eth_1h), " 1d:", len(eth_1d))'''),
    md("## 2. Simple trend + momentum"),
    code('''from analysis.indicators import add_all
d = add_all(eth_1d).dropna()
last = d.iloc[-1]
print("close:", last.close, " sma_50:", round(last.sma_50,2),
      " sma_200:", round(last.sma_200,2), " rsi:", round(last.rsi_14,2))'''),
    md("## 3. Score each factor"),
    code('''score = 0
if last.close > last.sma_50: score += 1
if last.sma_50 > last.sma_200: score += 1
if last.rsi_14 < 30: score += 1      # oversold, buy signal
if last.rsi_14 > 70: score -= 1      # overbought
if last.macd_hist > 0: score += 1
if last.macd_hist < 0: score -= 1

print("composite score:", score, "(range -3 to +4)")'''),
    md("## 4. Final action"),
    code('''if score >= 3:
    action, reason = "LONG", "strong bullish alignment"
elif score <= -2:
    action, reason = "SHORT", "strong bearish alignment"
else:
    action, reason = "FLAT", "no clear edge"

sig = action_block("ETHUSDT DASHBOARD", action, reason,
    price=float(last.close), conf=min(1.0, abs(score)/4),
    extra={"score": score})

(OUT/"signal_dashboard.json").write_text(json.dumps(sig, indent=2, default=str))
print("wrote signal_dashboard.json")''')
])

# ================================================================
# 02 single asset
# ================================================================
save("02_single_asset.ipynb", [
    md("# 02 - Single Asset (ETH only)\n\nDeep dive on ETH without any other market.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Fetch"),
    code('''eth_1d = fetch("ETHUSDT", "1d", 500)
print("rows:", len(eth_1d), " last:", eth_1d.index[-1].date())'''),
    md("## 2. Load from DB (6 years)"),
    code('''hist = sql("SELECT open_time, close FROM ohlcv WHERE symbol='ETHUSDT' AND timeframe='1d' ORDER BY open_time")
hist["date"] = pd.to_datetime(hist.open_time, unit="ms")
hist = hist.set_index("date")["close"]
print("range:", hist.index.min().date(), "->", hist.index.max().date(), "n=", len(hist))'''),
    md("## 3. Rolling stats"),
    code('''r = hist.pct_change().dropna()
print("mean daily:", f"{r.mean()*100:+.4f}%")
print("std daily :", f"{r.std()*100:.4f}%")
print("annualized vol:", f"{r.std()*np.sqrt(365)*100:.2f}%")
print("sharpe:", f"{r.mean()/r.std()*np.sqrt(365):.2f}")'''),
    md("## 4. Levels — support / resistance"),
    code('''recent = eth_1d.tail(60)
support = recent["low"].min()
resistance = recent["high"].max()
print(f"60d support    : {support:.2f}")
print(f"60d resistance : {resistance:.2f}")
print(f"current        : {float(eth_1d.close.iloc[-1]):.2f}")
print(f"range position : {(eth_1d.close.iloc[-1] - support)/(resistance - support)*100:.1f}%")'''),
    md("## 5. Action"),
    code('''cur = float(eth_1d.close.iloc[-1])
pos = (cur - support) / (resistance - support)

if pos < 0.2:
    action, reason = "LONG", "near 60d support — bounce zone"
elif pos > 0.8:
    action, reason = "SHORT", "near 60d resistance — fade zone"
else:
    action, reason = "FLAT", "mid-range — no edge"

action_block("ETH SINGLE ASSET", action, reason,
    price=cur, extra={"range_pos": f"{pos*100:.1f}%"})''')
])

# ================================================================
# 03 BTC correlation
# ================================================================
save("03_btc_correlation.ipynb", [
    md("# 03 - BTC Correlation\n\nHow much does BTC drive ETH? Lead/lag analysis.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Fetch both"),
    code('''eth = fetch("ETHUSDT", "1d", 500)
btc = fetch("BTCUSDT", "1d", 500)
both = pd.concat([eth.close.rename("ETH"), btc.close.rename("BTC")], axis=1).dropna()
print("rows:", len(both))'''),
    md("## 2. Returns correlation"),
    code('''r = both.pct_change().dropna()
print("corr (contemporary):", round(r.corr().iloc[0,1], 4))'''),
    md("## 3. Lead/lag — does BTC lead ETH?"),
    code('''lags = range(-5, 6)
cors = [r["BTC"].shift(l).corr(r["ETH"]) for l in lags]
best = list(lags)[int(np.argmax(cors))]
print("best lag (BTC leads ETH if negative):", best)
for l, c in zip(lags, cors):
    print(f"  lag {l:+d}: {c:+.4f}")'''),
    md("## 4. Chart — rolling 30d correlation"),
    code('''roll_corr = r["ETH"].rolling(30).corr(r["BTC"])
fig, ax = plt.subplots()
roll_corr.plot(ax=ax, color="steelblue", title="30d rolling ETH-BTC correlation")
ax.axhline(0, color="black", lw=0.5)
plt.tight_layout(); plt.show()'''),
    md("## 5. BTC-derived ETH signal"),
    code('''btc_ret_today = r["BTC"].iloc[-1]
eth_ret_today = r["ETH"].iloc[-1]
btc_momentum = r["BTC"].tail(5).mean()

if btc_momentum > 0.01:
    action, reason = "LONG", "BTC 5d momentum positive — alt tailwind"
elif btc_momentum < -0.01:
    action, reason = "SHORT", "BTC 5d momentum negative — alt headwind"
else:
    action, reason = "FLAT", "BTC flat — no signal"

action_block("ETH via BTC", action, reason,
    price=float(both["ETH"].iloc[-1]),
    extra={"btc_5d_mom": f"{btc_momentum*100:+.2f}%",
           "corr_30d": f"{roll_corr.iloc[-1]:.3f}"})''')
])

# ================================================================
# 04 news
# ================================================================
save("04_news_sentiment.ipynb", [
    md("# 04 - News Sentiment\n\nCheck the news table for recent sentiment.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Load news from DB"),
    code('''try:
    news = sql("SELECT ts, source, title, sentiment FROM news ORDER BY ts DESC LIMIT 100")
    news["date"] = pd.to_datetime(news.ts, unit="ms")
    print("rows:", len(news))
    news.head(10)
except Exception as e:
    print("news table empty or missing:", e)
    news = pd.DataFrame()'''),
    md("## 2. Sentiment distribution"),
    code('''if not news.empty and "sentiment" in news.columns:
    fig, ax = plt.subplots(figsize=(10, 3))
    news["sentiment"].dropna().hist(bins=30, ax=ax, color="steelblue", edgecolor="white")
    ax.axvline(0, color="black", lw=0.8)
    ax.set_title("news sentiment distribution")
    plt.tight_layout(); plt.show()'''),
    md("## 3. Recent news score"),
    code('''if not news.empty and "sentiment" in news.columns:
    recent = news.head(20)
    avg = float(recent["sentiment"].mean())
    print(f"avg sentiment (last 20): {avg:+.3f}")
else:
    avg = 0.0
    print("no sentiment data — treating as neutral")'''),
    md("## 4. Action"),
    code('''if avg > 0.2:   action, reason = "LONG", "positive news sentiment"
elif avg < -0.2: action, reason = "SHORT", "negative news sentiment"
else:            action, reason = "FLAT", "neutral news — no edge"
action_block("NEWS SENTIMENT", action, reason, conf=abs(avg))''')
])

# ================================================================
# 05 corrections
# ================================================================
save("05_correction_analysis.ipynb", [
    md("# 05 - Correction Analysis\n\nHow deep is the current drawdown vs historical?\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Load 6y history"),
    code('''h = sql("SELECT open_time, close FROM ohlcv WHERE symbol='ETHUSDT' AND timeframe='1d' ORDER BY open_time")
h["date"] = pd.to_datetime(h.open_time, unit="ms")
h = h.set_index("date")["close"]
print("n=", len(h))'''),
    md("## 2. Drawdown series"),
    code('''peak = h.cummax()
dd = h / peak - 1
print(f"current drawdown: {dd.iloc[-1]*100:+.2f}%")
print(f"worst ever      : {dd.min()*100:+.2f}%")
print(f"on              : {dd.idxmin().date()}")'''),
    md("## 3. Historical corrections > 20%"),
    code('''underwater = dd < -0.20
runs = []
start = None
for dt, u in underwater.items():
    if u and start is None: start = dt
    elif not u and start is not None:
        dur = (dt - start).days
        depth = dd[start:dt].min()
        runs.append({"start": start.date(), "end": dt.date(),
                     "days": dur, "depth": float(depth)})
        start = None
if start is not None:
    runs.append({"start": start.date(), "end": None, "days": (h.index[-1]-start).days,
                 "depth": float(dd[start:].min())})
pd.DataFrame(runs).tail(10)'''),
    md("## 4. Chart"),
    code('''fig, ax = plt.subplots(figsize=(13, 3))
dd.plot(ax=ax, color="crimson", title="historical drawdown")
ax.fill_between(dd.index, dd, 0, color="crimson", alpha=0.15)
plt.tight_layout(); plt.show()'''),
    md("## 5. Action"),
    code('''cur_dd = float(dd.iloc[-1])
if cur_dd < -0.40: action, reason = "LONG",  "deep correction — mean reversion zone"
elif cur_dd < -0.20: action, reason = "LONG",  "moderate correction — accumulate"
elif cur_dd > -0.05: action, reason = "FLAT",  "near all-time high — no correction edge"
else:                action, reason = "FLAT",  "shallow correction"
action_block("CORRECTION", action, reason,
    price=float(h.iloc[-1]), extra={"current_dd": f"{cur_dd*100:.2f}%"})''')
])

# ================================================================
# 06 volume
# ================================================================
save("06_volume_prediction.ipynb", [
    md("# 06 - Volume Prediction\n\nVolume leads price. Detect surges.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Load volume history"),
    code('''v = sql("SELECT open_time, close, volume FROM ohlcv WHERE symbol='ETHUSDT' AND timeframe='1d' ORDER BY open_time")
v["date"] = pd.to_datetime(v.open_time, unit="ms")
v = v.set_index("date").drop(columns="open_time")
print("n=", len(v))'''),
    md("## 2. Volume z-score"),
    code('''v["vol_z"] = (v["volume"] - v["volume"].rolling(50).mean()) / v["volume"].rolling(50).std()
print("current volume z-score:", round(v["vol_z"].iloc[-1], 2))
print("last 5 z-scores:")
print(v["vol_z"].tail(5))'''),
    md("## 3. Price effect of high-volume days"),
    code('''v["ret"] = v["close"].pct_change()
high_vol = v[v["vol_z"] > 1.5]["ret"].dropna()
low_vol  = v[v["vol_z"] < -1.0]["ret"].dropna()
print(f"high-vol mean return : {high_vol.mean()*100:+.3f}%  (n={len(high_vol)})")
print(f"low-vol mean return  : {low_vol.mean()*100:+.3f}%  (n={len(low_vol)})")'''),
    md("## 4. Action"),
    code('''z = float(v["vol_z"].iloc[-1])
ret_today = float(v["ret"].iloc[-1])
if z > 1.5 and ret_today > 0:   action, reason = "LONG",  "high volume + up day — continuation"
elif z > 1.5 and ret_today < 0: action, reason = "SHORT", "high volume + down day — capitulation"
else:                            action, reason = "FLAT",  "normal volume — no signal"
action_block("VOLUME", action, reason,
    price=float(v["close"].iloc[-1]), extra={"vol_z": f"{z:.2f}"})''')
])

# ================================================================
# 07 volatility
# ================================================================
save("07_volatility.ipynb", [
    md("# 07 - Volatility Regimes\n\nHigh vol clusters with high vol. Detect the regime.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Load"),
    code('''v = sql("SELECT open_time, close FROM ohlcv WHERE symbol='ETHUSDT' AND timeframe='1d' ORDER BY open_time")
v["date"] = pd.to_datetime(v.open_time, unit="ms")
v = v.set_index("date").drop(columns="open_time")
v["ret"] = v["close"].pct_change()
v["vol30"] = v["ret"].rolling(30).std() * np.sqrt(365)
print(v.tail(3))'''),
    md("## 2. Current vs historical"),
    code('''cur_vol = float(v["vol30"].iloc[-1])
pct = float((v["vol30"].dropna() < cur_vol).mean())
print(f"current 30d vol: {cur_vol*100:.2f}%")
print(f"percentile     : {pct*100:.1f}%")
if pct > 0.8: print("regime: HIGH vol")
elif pct < 0.2: print("regime: LOW vol")
else: print("regime: NORMAL vol")'''),
    md("## 3. Chart"),
    code('''fig, ax = plt.subplots(figsize=(13, 3))
v["vol30"].plot(ax=ax, color="darkorange", title="30d annualized volatility")
ax.axhline(cur_vol, ls=":", color="black")
plt.tight_layout(); plt.show()'''),
    md("## 4. Action"),
    code('''if pct > 0.85:   action, reason = "FLAT", "high vol — reduce size"
elif pct < 0.15: action, reason = "LONG", "low vol — trend likely, buy breakouts"
else:            action, reason = "FLAT", "normal vol"
action_block("VOLATILITY REGIME", action, reason,
    price=float(v["close"].iloc[-1]), extra={"vol_pct": f"{pct*100:.1f}%"})''')
])

# ================================================================
# 08 funding + OI
# ================================================================
save("08_funding_oi.ipynb", [
    md("# 08 - Funding & Open Interest\n\nCrowded positioning → reversal signal.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Load funding + OI"),
    code('''fr = sql("SELECT ts, rate FROM funding_rate ORDER BY ts")
fr["date"] = pd.to_datetime(fr.ts, unit="ms"); fr = fr.set_index("date")["rate"]
oi = sql("SELECT ts, oi FROM open_interest ORDER BY ts")
oi["date"] = pd.to_datetime(oi.ts, unit="ms"); oi = oi.set_index("date")["oi"]
print("funding n=", len(fr), " oi n=", len(oi))'''),
    md("## 2. Current funding"),
    code('''cur_fr = float(fr.iloc[-1])
print(f"latest funding: {cur_fr*100:+.4f}% per 8h")
if cur_fr > 0.0005: print("> longs pay shorts — crowded long")
elif cur_fr < -0.0005: print("> shorts pay longs — crowded short")
else: print("> neutral")'''),
    md("## 3. OI change"),
    code('''oi_chg = (oi.iloc[-1] / oi.iloc[-8] - 1) * 100
print(f"OI change (last 7d): {oi_chg:+.2f}%")'''),
    md("## 4. Action"),
    code('''if cur_fr > 0.001 and oi_chg > 5:    action, reason = "SHORT", "crowded long — squeeze risk"
elif cur_fr < -0.001 and oi_chg > 5:  action, reason = "LONG",  "crowded short — squeeze up"
else:                                  action, reason = "FLAT",  "positioning neutral"
action_block("FUNDING / OI", action, reason,
    extra={"funding": f"{cur_fr*100:+.4f}%", "oi_7d_chg": f"{oi_chg:+.2f}%"})''')
])

# ================================================================
# 09 fear greed
# ================================================================
save("09_fear_greed.ipynb", [
    md("# 09 - Fear & Greed\n\nContrarian: extreme readings reverse.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Load F&G"),
    code('''fg = sql("SELECT ts, value, label FROM fear_greed ORDER BY ts")
fg["date"] = pd.to_datetime(fg.ts, unit="ms")
fg = fg.set_index("date").drop(columns="ts")
print("n=", len(fg), " last:", fg.index[-1].date(), " value:", int(fg.iloc[-1]["value"]))'''),
    md("## 2. Historical bands"),
    code('''extreme_fear = fg[fg.value < 20]
extreme_greed = fg[fg.value > 80]
print(f"days in extreme fear : {len(extreme_fear)}")
print(f"days in extreme greed: {len(extreme_greed)}")'''),
    md("## 3. Next-day return by F&G band"),
    code('''px = sql("SELECT open_time, close FROM ohlcv WHERE symbol='ETHUSDT' AND timeframe='1d' ORDER BY open_time")
px["date"] = pd.to_datetime(px.open_time, unit="ms")
px = px.set_index("date")["close"]
r_next = px.pct_change().shift(-1)
merged = pd.concat([fg.value, r_next], axis=1).dropna()
merged.columns = ["fng", "ret_next"]
merged["band"] = pd.cut(merged.fng, [0,20,40,60,80,100],
                        labels=["extreme fear","fear","neutral","greed","extreme greed"])
merged.groupby("band", observed=True)["ret_next"].agg(["mean","count"])'''),
    md("## 4. Action"),
    code('''v = int(fg.iloc[-1]["value"])
if v < 20:   action, reason = "LONG",  "extreme fear — contrarian buy"
elif v > 80: action, reason = "SHORT", "extreme greed — contrarian sell"
else:        action, reason = "FLAT",  "F&G neutral"
action_block("FEAR & GREED", action, reason, extra={"fng": v})''')
])

# ================================================================
# 10 onchain
# ================================================================
save("10_onchain.ipynb", [
    md("# 10 - Onchain Metrics\n\nActive addresses, gas, staking.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Load"),
    code('''try:
    oc = sql("SELECT metric, ts, value FROM onchain ORDER BY ts")
    oc["date"] = pd.to_datetime(oc.ts, unit="ms")
    print("metrics:", oc.metric.unique().tolist())
    print("rows:", len(oc))
except Exception as e:
    print("onchain empty:", e)
    oc = pd.DataFrame()'''),
    md("## 2. Latest values"),
    code('''if not oc.empty:
    latest = oc.sort_values("ts").groupby("metric").tail(1)
    print(latest[["metric","value"]])'''),
    md("## 3. Action"),
    code('''if not oc.empty and "eth_staked" in oc.metric.values:
    staked = oc[oc.metric=="eth_staked"].sort_values("ts")
    chg = (staked.value.iloc[-1] / staked.value.iloc[-30] - 1)*100 if len(staked)>30 else 0
    if chg > 1:   action, reason = "LONG", "staking inflow rising"
    else:         action, reason = "FLAT", "staking flat"
else:
    action, reason = "FLAT", "no onchain signal available"
action_block("ONCHAIN", action, reason)''')
])

# ================================================================
# 11 orderbook
# ================================================================
save("11_orderbook.ipynb", [
    md("# 11 - Order Book Imbalance\n\nBid vs ask depth.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Load orderbook snapshot"),
    code('''ob = sql("SELECT ts, bid_price, bid_qty, ask_price, ask_qty FROM orderbook ORDER BY ts DESC LIMIT 40")
print("rows:", len(ob))
if not ob.empty:
    latest_ts = ob.ts.max()
    snap = ob[ob.ts == latest_ts]
    bid_vol = snap.bid_qty.sum()
    ask_vol = snap.ask_qty.sum()
    imb = (bid_vol - ask_vol) / (bid_vol + ask_vol)
    print(f"bid vol: {bid_vol:.3f}")
    print(f"ask vol: {ask_vol:.3f}")
    print(f"imbalance: {imb:+.4f}")'''),
    md("## 2. Action"),
    code('''if len(ob) == 0:
    action, reason = "FLAT", "no orderbook data"
elif imb > 0.3:   action, reason = "LONG",  "bids dominate — buy pressure"
elif imb < -0.3:  action, reason = "SHORT", "asks dominate — sell pressure"
else:             action, reason = "FLAT",  "balanced book"
action_block("ORDERBOOK", action, reason, extra={"imbalance": f"{imb:+.3f}" if len(ob) else "n/a"})''')
])

# ================================================================
# 12 multi factor
# ================================================================
save("12_multi_factor.ipynb", [
    md("# 12 - Multi-Factor Signal\n\nCombine every factor into one vote.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Fetch everything"),
    code('''eth = fetch("ETHUSDT", "1d", 500)
from analysis.indicators import add_all
d = add_all(eth).dropna()
last = d.iloc[-1]
print("price:", last.close)'''),
    md("## 2. Vote tally"),
    code('''votes = {}

# 1. trend
votes["trend"] = 1 if last.close > last.sma_50 else -1
# 2. long-term trend
votes["trend_lt"] = 1 if last.sma_50 > last.sma_200 else -1
# 3. RSI
votes["rsi"] = 1 if last.rsi_14 < 30 else (-1 if last.rsi_14 > 70 else 0)
# 4. MACD
votes["macd"] = 1 if last.macd_hist > 0 else -1
# 5. drawdown
dd = (last.close / d.close.cummax().iloc[-1] - 1)
votes["drawdown"] = 1 if dd < -0.3 else 0
# 6. funding
try:
    fr = sql("SELECT rate FROM funding_rate ORDER BY ts DESC LIMIT 1")["rate"].iloc[0]
    votes["funding"] = -1 if fr > 0.001 else (1 if fr < -0.001 else 0)
except: votes["funding"] = 0
# 7. F&G
try:
    fg = sql("SELECT value FROM fear_greed ORDER BY ts DESC LIMIT 1")["value"].iloc[0]
    votes["fng"] = 1 if fg < 20 else (-1 if fg > 80 else 0)
except: votes["fng"] = 0

for k, v in votes.items():
    print(f"  {k:<12} {v:+d}")'''),
    md("## 3. Composite"),
    code('''total = sum(votes.values())
print("total votes:", total, " (range", -len(votes), "to", len(votes), ")")
print("bullish votes:", sum(1 for v in votes.values() if v > 0))
print("bearish votes:", sum(1 for v in votes.values() if v < 0))'''),
    md("## 4. Action"),
    code('''if total >= 3:   action, reason = "LONG",  f"strong bullish ({total} votes)"
elif total <= -3: action, reason = "SHORT", f"strong bearish ({total} votes)"
else:            action, reason = "FLAT",  f"mixed ({total} votes)"
action_block("MULTI-FACTOR", action, reason,
    price=float(last.close), conf=min(1.0, abs(total)/len(votes)),
    extra={"votes": total})''')
])

# ================================================================
# 13 full desk
# ================================================================
save("13_full_desk.ipynb", [
    md("# 13 - Full Desk\n\nEvery factor → single decision.\n"),
    md("## Setup"), code(SETUP),
    md("## 1. Fetch"),
    code('''eth = fetch("ETHUSDT", "1d", 500)
from analysis.indicators import add_all
d = add_all(eth).dropna()
print("price:", d.close.iloc[-1])'''),
    md("## 2. All signals"),
    code('''signals = {}
last = d.iloc[-1]

signals["trend"]    = 1 if last.close > last.sma_50 else -1
signals["rsi"]      = 1 if last.rsi_14 < 30 else (-1 if last.rsi_14 > 70 else 0)
signals["macd"]     = 1 if last.macd_hist > 0 else -1
signals["momentum"] = 1 if d.close.pct_change(20).iloc[-1] > 0 else -1

try:
    fg = sql("SELECT value FROM fear_greed ORDER BY ts DESC LIMIT 1")["value"].iloc[0]
    signals["fng"] = 1 if fg < 20 else (-1 if fg > 80 else 0)
except: signals["fng"] = 0

try:
    fr = sql("SELECT rate FROM funding_rate ORDER BY ts DESC LIMIT 1")["rate"].iloc[0]
    signals["funding"] = -1 if fr > 0.001 else (1 if fr < -0.001 else 0)
except: signals["funding"] = 0

for k, v in signals.items():
    print(f"  {k:<12} {v:+d}")'''),
    md("## 3. Visual"),
    code('''fig, ax = plt.subplots(figsize=(10, 3))
names = list(signals.keys())
vals = list(signals.values())
colors = ["seagreen" if v>0 else "crimson" if v<0 else "gray" for v in vals]
ax.barh(names, vals, color=colors)
ax.axvline(0, color="black", lw=0.8)
ax.set_xlim(-1.5, 1.5)
ax.set_title("signal votes")
plt.tight_layout(); plt.show()'''),
    md("## 4. Score"),
    code('''score = sum(signals.values())
max_score = len(signals)
print(f"score: {score:+d} / {max_score}")'''),
    md("## 5. Confidence"),
    code('''conf = abs(score) / max_score
print(f"confidence: {conf:.2f}")'''),
    md("## 6. Trend filter override"),
    code('''trend_ok = last.close > last.sma_50
if score > 0 and not trend_ok:
    print("up signal but downtrend -> downgrade")
    score = 0
elif score < 0 and trend_ok:
    print("down signal but uptrend -> downgrade")
    score = 0'''),
    md("## 7. Position sizing"),
    code('''ACCOUNT = 1000.0
RISK_PCT = 1.0
atr = float(last.atr_14)
stop_dist = 1.5 * atr
entry = float(last.close)
risk_usd = ACCOUNT * RISK_PCT / 100
size = risk_usd / stop_dist'''),
    md("## 8. Compose final"),
    code('''if score >= 3:
    action = "LONG"
    stop, target = entry - stop_dist, entry + 2*stop_dist
    reason = f"{score} bullish signals + uptrend"
elif score <= -3:
    action = "SHORT"
    stop, target = entry + stop_dist, entry - 2*stop_dist
    reason = f"{score} bearish signals + downtrend"
else:
    action = "FLAT"
    stop = target = entry
    reason = f"weak signal ({score})"
    size = 0

print(f"action: {action}")'''),
    md("## 9. Risk warnings"),
    code('''warn = []
if conf < 0.3: warn.append("low confidence")
if abs(score) < 3: warn.append("weak composite")
if atr/entry > 0.05: warn.append("high ATR — size down")
for w in warn: print(" !", w)
if not warn: print(" no warnings")'''),
    md("## 10. Final action block"),
    code('''sig = action_block("ETH FULL DESK", action, reason,
    price=entry, conf=conf,
    entry=entry, stop=stop, target=target,
    extra={"size": f"{size:.4f} ETH", "risk": f"${risk_usd:.2f}"})

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
(OUT/f"trade_full_{ts}.json").write_text(json.dumps(sig, indent=2, default=str))
print("wrote", OUT/f"trade_full_{ts}.json")'''),
    md("## 11. One-line summary"),
    code('''if action == "FLAT":
    line = f"FLAT  |  {reason}  |  conf {conf:.2f}"
else:
    line = f"{action}  |  entry {entry:.2f}  stop {stop:.2f}  target {target:.2f}  |  conf {conf:.2f}"
print()
print(">>>", line)
print()
print("END OF RUN")''')
])

print()
print(f"folder: {DIR}")
for p in sorted(DIR.glob("*.ipynb")):
    print(" ", p.name)