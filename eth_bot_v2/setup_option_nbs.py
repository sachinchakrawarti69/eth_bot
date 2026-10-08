"""
Create analysis/option_notebook/ with a clean set of notebooks.

Structure:
  analysis/option_notebook/
  ├── README.md
  ├── __init__.py
  ├── 01_chain_snapshot.ipynb
  ├── 02_iv_smile.ipynb
  ├── 03_iv_surface.ipynb
  ├── 04_put_call_ratio.ipynb
  ├── 05_skew_term.ipynb
  ├── 06_iv_vs_realized.ipynb
  ├── 07_max_pain.ipynb
  ├── 08_greeks.ipynb
  └── 09_dashboard.ipynb

Run:
    python setup_option_nbs.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPT = ROOT / "analysis" / "option_notebook"


# ============================================================
# setup cell shared by every notebook
# ============================================================

SETUP = '''import sys, sqlite3
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_p = Path.cwd().resolve()
while _p != _p.parent and not (_p / "database").exists():
    _p = _p.parent
sys.path.insert(0, str(_p))

OPT_DB = _p / "database" / "options.db"
MKT_DB = _p / "database" / "market.db"

pd.set_option("display.width", 180)
pd.set_option("display.max_columns", 60)
plt.rcParams["figure.figsize"] = (13, 4)
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3

def opt(q, **p):
    with sqlite3.connect(OPT_DB) as c:
        return pd.read_sql_query(q, c, params=p)

def mkt(q, **p):
    with sqlite3.connect(MKT_DB) as c:
        return pd.read_sql_query(q, c, params=p)

print("options.db:", OPT_DB)
print("market.db :", MKT_DB)'''


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}


def code(s):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": s.splitlines(keepends=True)}


def notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }


# ============================================================
# 01 - chain snapshot
# ============================================================

nb01 = [
    md("""# 01 - Chain Snapshot

Load the full option chain for one underlying at the latest snapshot.

Shows:
- every strike and expiry currently active
- mark price, bid/ask, IV, OI, volume
- underlying spot at snapshot time
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Latest snapshot"),
    code('''oc = opt("""
    SELECT * FROM option_chain
    WHERE underlying='ETH'
      AND ts = (SELECT MAX(ts) FROM option_chain WHERE underlying='ETH')
    ORDER BY expiry, strike, kind
""")
print("rows:", len(oc))
if not oc.empty:
    print("snapshot:", oc.date.iloc[0])
    print("expiries:", oc.expiry.nunique())
    print("strikes :", oc.strike.nunique())
oc.head(20)'''),
    md("## 2. Expiry summary"),
    code('''if not oc.empty:
    oc["expiry_date"] = pd.to_datetime(oc.expiry, unit="ms").dt.date
    summary = oc.groupby("expiry_date").agg(
        instruments=("strike", "count"),
        strikes=("strike", "nunique"),
        total_oi=("oi", "sum"),
        total_vol=("volume", "sum"),
    )
    summary'''),
    md("## 3. Spot price"),
    code('''if not oc.empty:
    print("underlying spot:", oc.underlying_px.iloc[0])'''),
]

# ============================================================
# 02 - IV smile
# ============================================================

nb02 = [
    md("""# 02 - IV Smile

Implied volatility across strikes for one expiry.

Classic shape: a "smile" or "skew" — out-of-the-money options have higher IV
than at-the-money.

Reads `implied_volatility` for the nearest expiry.
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Load IV for nearest expiry"),
    code('''iv = opt("""
    SELECT * FROM implied_volatility
    WHERE underlying='ETH'
      AND ts = (SELECT MAX(ts) FROM implied_volatility WHERE underlying='ETH')
    ORDER BY expiry, strike
""")
print("rows:", len(iv))
iv["dte"] = iv.dte.astype(float)
iv = iv[iv.dte > 0]
valid_expiries = iv.groupby("expiry").size().sort_index()
print("expiries available:")
print(valid_expiries)'''),
    md("## 2. Pick one expiry, plot the smile"),
    code('''if not iv.empty:
    target = iv.expiry.iloc[0]
    snap = iv[iv.expiry == target]
    dte_days = round(float(snap.dte.iloc[0]), 1)

    fig, ax = plt.subplots()
    for kind, color in [("C", "seagreen"), ("P", "crimson")]:
        s = snap[snap["kind"] == kind].sort_values("strike")
        ax.plot(s.strike, s.iv * 100, "o-", color=color,
                label="Calls" if kind == "C" else "Puts")
    ax.set_title(f"IV smile — expiry {pd.to_datetime(target, unit='ms').date()}  ({dte_days}d)")
    ax.set_xlabel("strike")
    ax.set_ylabel("IV %")
    ax.legend()
    plt.tight_layout()
    plt.show()'''),
    md("## 3. ATM IV + skew"),
    code('''if not iv.empty:
    spot = iv.iv.iloc[0]
    # ATM = strike nearest spot - we use underlying_px if present, else skip
    oc = opt("""
        SELECT underlying_px FROM option_chain
        WHERE underlying='ETH'
        ORDER BY ts DESC LIMIT 1
    """)
    spot = float(oc.underlying_px.iloc[0]) if not oc.empty and oc.underlying_px.iloc[0] else None

    if spot:
        target = iv.expiry.iloc[0]
        snap = iv[iv.expiry == target].copy()
        atm_row = snap.iloc[(snap.strike - spot).abs().argsort()[:1]]
        print(f"spot  = {spot:.2f}")
        print(f"ATM strike ~ {atm_row.strike.iloc[0]:.0f}")
        print(f"ATM IV = {atm_row.iv.iloc[0]*100:.2f}%")'''),
]

# ============================================================
# 03 - IV surface
# ============================================================

nb03 = [
    md("""# 03 - IV Surface

Heatmap of IV across **strike × expiry**.

Rows = expiry dates, columns = strikes, color = IV%.
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Load IV snapshot"),
    code('''iv = opt("""
    SELECT * FROM implied_volatility
    WHERE underlying='ETH'
      AND ts = (SELECT MAX(ts) FROM implied_volatility WHERE underlying='ETH')
""")
print("rows:", len(iv))
iv["dte"] = iv.dte.astype(float)
iv = iv[(iv.dte > 0) & (iv.dte < 200)]'''),
    md("## 2. IV surface heatmap"),
    code('''if not iv.empty:
    pivot = iv.pivot_table(index="expiry", columns="strike",
                           values="iv", aggfunc="mean")
    if not pivot.empty:
        fig, ax = plt.subplots(figsize=(13, 6))
        im = ax.imshow(pivot.values * 100, aspect="auto", cmap="viridis")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([pd.to_datetime(e, unit="ms").date() for e in pivot.index])
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([f"{int(s)}" for s in pivot.columns], rotation=45)
        plt.colorbar(im, ax=ax, label="IV %")
        ax.set_title("IV surface — strikes × expiries")
        ax.set_xlabel("strike")
        ax.set_ylabel("expiry")
        plt.tight_layout()
        plt.show()'''),
    md("## 3. Term structure (ATM IV per expiry)"),
    code('''if not iv.empty:
    # ATM IV per expiry = strike nearest underlying
    oc = opt("SELECT underlying_px FROM option_chain ORDER BY ts DESC LIMIT 1")
    spot = float(oc.underlying_px.iloc[0]) if not oc.empty else None

    if spot:
        rows = []
        for e, g in iv.groupby("expiry"):
            atm = g.iloc[(g.strike - spot).abs().argsort()[:1]]
            dte = float(g.dte.iloc[0])
            rows.append({"expiry": pd.to_datetime(e, unit="ms").date(),
                         "dte": dte, "atm_iv": float(atm.iv.iloc[0])})
        ts_df = pd.DataFrame(rows).sort_values("dte")

        fig, ax = plt.subplots()
        ax.plot(ts_df.dte, ts_df.atm_iv * 100, "o-", color="purple")
        ax.set_title("ATM IV term structure")
        ax.set_xlabel("days to expiry")
        ax.set_ylabel("IV %")
        plt.tight_layout()
        plt.show()
        ts_df'''),
]

# ============================================================
# 04 - put/call ratio
# ============================================================

nb04 = [
    md("""# 04 - Put/Call Ratio

PCR over time. High PCR = fear. Low PCR = greed.

Reads `option_summary`.
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Load summary"),
    code('''s = opt("SELECT * FROM option_summary WHERE underlying='ETH' ORDER BY ts")
print("rows:", len(s))
s["date_dt"] = pd.to_datetime(s.ts, unit="ms")
s = s.set_index("date_dt")
s[["pcr_oi", "pcr_vol"]].tail(10)'''),
    md("## 2. PCR chart"),
    code('''if not s.empty:
    fig, ax = plt.subplots()
    ax.plot(s.index, s.pcr_oi, "o-", color="steelblue", label="PCR (OI)")
    ax.plot(s.index, s.pcr_vol, "s-", color="darkorange", label="PCR (volume)")
    ax.axhline(1.0, ls="--", color="gray", lw=0.8)
    ax.set_title("ETH put/call ratio")
    ax.set_ylabel("ratio")
    ax.legend()
    plt.tight_layout()
    plt.show()'''),
    md("## 3. Current reading"),
    code('''if not s.empty:
    last = s.iloc[-1]
    print(f"as of       : {last.name}")
    print(f"PCR (OI)    : {last.pcr_oi}")
    print(f"PCR (volume): {last.pcr_vol}")
    if last.pcr_oi > 1.3:   state = "extreme fear"
    elif last.pcr_oi > 1.0: state = "fear"
    elif last.pcr_oi > 0.7: state = "neutral"
    else:                    state = "greed"
    print(f"state       : {state}")'''),
]

# ============================================================
# 05 - skew and term
# ============================================================

nb05 = [
    md("""# 05 - Skew & Term Structure

- **Skew**: difference between OTM put IV and OTM call IV (25-delta)
- **Term structure**: short-dated IV minus long-dated IV

Both are regime indicators.
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Load summary"),
    code('''s = opt("SELECT * FROM option_summary WHERE underlying='ETH' ORDER BY ts")
s["date_dt"] = pd.to_datetime(s.ts, unit="ms")
s = s.set_index("date_dt")'''),
    md("## 2. Skew & term charts"),
    code('''if not s.empty:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4))
    if s.iv_25d_skew.notna().any():
        a1.plot(s.index, s.iv_25d_skew * 100, "o-", color="purple")
        a1.axhline(0, ls="--", color="black", lw=0.8)
    a1.set_title("25-delta skew")
    a1.set_ylabel("%")

    if s.term_structure.notna().any():
        a2.plot(s.index, s.term_structure * 100, "o-", color="darkorange")
        a2.axhline(0, ls="--", color="black", lw=0.8)
    a2.set_title("term structure (7d - 30d)")
    a2.set_ylabel("%")
    plt.tight_layout()
    plt.show()'''),
    md("## 3. Compute skew from raw chain"),
    code('''iv = opt("""
    SELECT * FROM implied_volatility
    WHERE underlying='ETH'
      AND ts = (SELECT MAX(ts) FROM implied_volatility WHERE underlying='ETH')
""")
oc = opt("SELECT underlying_px FROM option_chain ORDER BY ts DESC LIMIT 1")
spot = float(oc.underlying_px.iloc[0]) if not oc.empty else None

if spot:
    target_expiry = iv.expiry.iloc[0]
    snap = iv[iv.expiry == target_expiry].copy()
    near = snap.iloc[(snap.strike - spot).abs().argsort()[:5]]
    print("nearest 5 strikes to spot:")
    print(near[["strike", "kind", "iv"]].sort_values(["kind", "strike"]))'''),
]

# ============================================================
# 06 - IV vs realized vol
# ============================================================

nb06 = [
    md("""# 06 - IV vs Realized Vol

Is IV overpricing or underpricing future realized volatility?

If IV > RV → options are expensive (sell vol).
If IV < RV → options are cheap (buy vol).
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Load data"),
    code('''s = opt("SELECT * FROM option_summary WHERE underlying='ETH' ORDER BY ts")
s["date_dt"] = pd.to_datetime(s.ts, unit="ms")
s = s.set_index("date_dt")

px = mkt("SELECT open_time, close FROM ohlcv WHERE symbol='ETHUSDT' AND timeframe='1d' ORDER BY open_time")
px["date_dt"] = pd.to_datetime(px.open_time, unit="ms")
px = px.set_index("date_dt")["close"]
print("summary rows:", len(s))
print("price rows  :", len(px))'''),
    md("## 2. Compute realized vol (30d)"),
    code('''r = px.pct_change()
rv = r.rolling(30).std() * np.sqrt(365)
rv.tail(3)'''),
    md("## 3. IV vs RV"),
    code('''if not s.empty and s.atm_iv.notna().any():
    fig, ax = plt.subplots()
    ax.plot(s.index, s.atm_iv * 100, "o-", color="crimson", label="ATM IV")
    ax.plot(rv.index, rv * 100, "-", color="steelblue", label="30d realized vol")
    ax.set_title("IV vs realized vol")
    ax.set_ylabel("vol %")
    ax.legend()
    plt.tight_layout()
    plt.show()'''),
    md("## 4. Vol premium"),
    code('''if not s.empty and s.atm_iv.notna().any():
    aligned = pd.concat([s.atm_iv.rename("iv"), rv.rename("rv")], axis=1).dropna()
    aligned["premium"] = aligned.iv - aligned.rv
    print(f"mean premium : {aligned.premium.mean()*100:+.2f} pp")
    print(f"last premium : {aligned.premium.iloc[-1]*100:+.2f} pp")
    aligned.tail()'''),
]

# ============================================================
# 07 - max pain
# ============================================================

nb07 = [
    md("""# 07 - Max Pain

The strike where option buyers would lose the most (i.e. the price
where the most options expire worthless).

Price tends to gravitate toward max pain near expiry.
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Load chain"),
    code('''oc = opt("""
    SELECT * FROM option_chain
    WHERE underlying='ETH'
      AND ts = (SELECT MAX(ts) FROM option_chain WHERE underlying='ETH')
""")
print("rows:", len(oc))'''),
    md("## 2. OI by strike"),
    code('''if not oc.empty:
    by_strike = oc.groupby("strike")["oi"].sum().sort_index()

    fig, ax = plt.subplots()
    ax.bar(by_strike.index, by_strike.values, width=20, color="steelblue")
    ax.set_title("total OI by strike")
    ax.set_xlabel("strike")
    ax.set_ylabel("OI")
    plt.tight_layout()
    plt.show()

    mp = int(by_strike.idxmax())
    print(f"max pain (highest OI strike) = {mp}")'''),
    md("## 3. Put vs call OI by strike"),
    code('''if not oc.empty:
    pivot = oc.pivot_table(index="strike", columns="kind",
                           values="oi", aggfunc="sum").fillna(0)
    pivot.plot.bar(stacked=True, figsize=(14, 4), color={"C": "seagreen", "P": "crimson"})
    plt.title("OI by strike — calls vs puts")
    plt.xlabel("strike")
    plt.tight_layout()
    plt.show()'''),
    md("## 4. Max pain over time"),
    code('''s = opt("SELECT * FROM option_summary WHERE underlying='ETH' ORDER BY ts")
if not s.empty:
    s["date_dt"] = pd.to_datetime(s.ts, unit="ms")
    fig, ax = plt.subplots()
    ax.plot(s.date_dt, s.max_pain, "o-", color="purple", label="max pain")
    ax.set_title("max pain over time")
    ax.set_ylabel("strike")
    ax.legend()
    plt.tight_layout()
    plt.show()'''),
]

# ============================================================
# 08 - greeks
# ============================================================

nb08 = [
    md("""# 08 - Greeks

Delta, gamma, theta, vega, rho for the option chain.

Requires fetching with `--greeks`:
    python -m scripts_python.fetch_options --currency ETH --greeks
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Load greeks"),
    code('''g = opt("SELECT * FROM greeks WHERE underlying='ETH' ORDER BY ts DESC LIMIT 500")
print("rows:", len(g))
if g.empty:
    print("no greeks — fetch with --greeks flag")
g.head()'''),
    md("## 2. Delta by strike"),
    code('''if not g.empty:
    snap = g[g.ts == g.ts.max()].copy()
    target = snap.expiry.iloc[0]
    s = snap[snap.expiry == target]

    fig, ax = plt.subplots()
    for kind, color in [("C", "seagreen"), ("P", "crimson")]:
        d = s[s["kind"] == kind].sort_values("strike")
        ax.plot(d.strike, d.delta, "o-", color=color,
                label="Call delta" if kind == "C" else "Put delta")
    ax.axhline(0, ls="--", color="black", lw=0.8)
    ax.set_title(f"delta by strike — {pd.to_datetime(target, unit='ms').date()}")
    ax.set_xlabel("strike")
    ax.set_ylabel("delta")
    ax.legend()
    plt.tight_layout()
    plt.show()'''),
    md("## 3. Gamma"),
    code('''if not g.empty:
    snap = g[g.ts == g.ts.max()].copy()
    target = snap.expiry.iloc[0]
    s = snap[snap.expiry == target].sort_values("strike")

    fig, ax = plt.subplots()
    ax.plot(s.strike, s.gamma, "o-", color="darkorange")
    ax.set_title("gamma by strike")
    ax.set_xlabel("strike")
    ax.set_ylabel("gamma")
    plt.tight_layout()
    plt.show()'''),
]

# ============================================================
# 09 - dashboard
# ============================================================

nb09 = [
    md("""# 09 - Options Dashboard

One view: everything about the current ETH options market.

Combines: PCR, ATM IV, skew, max pain, spot, trend.
"""),
    md("## Setup"),
    code(SETUP),
    md("## 1. Load data"),
    code('''s = opt("SELECT * FROM option_summary WHERE underlying='ETH' ORDER BY ts")
oc = opt("SELECT underlying_px FROM option_chain ORDER BY ts DESC LIMIT 1")
iv = opt("""
    SELECT * FROM implied_volatility
    WHERE underlying='ETH'
      AND ts = (SELECT MAX(ts) FROM implied_volatility WHERE underlying='ETH')
""")
print(f"summary rows: {len(s)}")
print(f"iv rows     : {len(iv)}")'''),
    md("## 2. Snapshot"),
    code('''if not s.empty:
    last = s.iloc[-1]
    spot = float(oc.underlying_px.iloc[0]) if not oc.empty and oc.underlying_px.iloc[0] else None

    print("=" * 55)
    print("  ETH OPTIONS DASHBOARD")
    print("=" * 55)
    print(f"  as of       : {pd.to_datetime(last.ts, unit='ms')}")
    if spot: print(f"  spot        : {spot:.2f}")
    print(f"  PCR (OI)    : {last.pcr_oi}")
    print(f"  PCR (vol)   : {last.pcr_vol}")
    print(f"  max pain    : {last.max_pain}")
    print(f"  put OI max  : {last.put_oi_max_strike}")
    print(f"  call OI max : {last.call_oi_max_strike}")
    print(f"  ATM IV      : {last.atm_iv}")
    print(f"  25d skew    : {last.iv_25d_skew}")
    print(f"  term struct : {last.term_structure}")
    print("=" * 55)'''),
    md("## 3. Signals"),
    code('''if not s.empty:
    last = s.iloc[-1]
    signals = []

    # PCR
    if last.pcr_oi and last.pcr_oi > 1.3:
        signals.append(("PCR", "bearish", "put-heavy"))
    elif last.pcr_oi and last.pcr_oi < 0.7:
        signals.append(("PCR", "bullish", "call-heavy"))
    else:
        signals.append(("PCR", "neutral", ""))

    # skew
    if last.iv_25d_skew and last.iv_25d_skew > 0.05:
        signals.append(("skew", "bearish", "puts expensive"))
    elif last.iv_25d_skew and last.iv_25d_skew < -0.02:
        signals.append(("skew", "bullish", "calls expensive"))
    else:
        signals.append(("skew", "neutral", ""))

    # max pain vs spot
    if last.max_pain and spot:
        dist = (last.max_pain - spot) / spot * 100
        if dist > 3:
            signals.append(("max pain", "bullish", f"+{dist:.1f}% above spot"))
        elif dist < -3:
            signals.append(("max pain", "bearish", f"{dist:.1f}% below spot"))
        else:
            signals.append(("max pain", "neutral", f"{dist:+.1f}%"))

    for name, sig, note in signals:
        print(f"  {name:<12} {sig:<10} {note}")'''),
    md("## 4. Composite"),
    code('''if not s.empty:
    bull = sum(1 for _, sig, _ in signals if sig == "bullish")
    bear = sum(1 for _, sig, _ in signals if sig == "bearish")
    neut = sum(1 for _, sig, _ in signals if sig == "neutral")

    print(f"bullish: {bull}")
    print(f"bearish: {bear}")
    print(f"neutral: {neut}")

    if bull > bear:   verdict = "NET BULLISH"
    elif bear > bull: verdict = "NET BEARISH"
    else:             verdict = "NEUTRAL"

    print()
    print(f"  >>> {verdict}  <<<")'''),
]


# ============================================================
# README
# ============================================================

README = """# analysis/option_notebook/

Options analysis notebooks. All read from `database/options.db`.

## Notebooks

| # | Notebook | Focus |
|---|---|---|
| 01 | chain_snapshot | Full chain for latest snapshot |
| 02 | iv_smile | IV across strikes, one expiry |
| 03 | iv_surface | IV heatmap, strike × expiry |
| 04 | put_call_ratio | PCR over time |
| 05 | skew_term | Skew and term structure |
| 06 | iv_vs_realized | Vol premium |
| 07 | max_pain | Max pain analysis |
| 08 | greeks | Delta, gamma, theta, vega |
| 09 | dashboard | Everything in one view |

## Prerequisites

Data must be in `database/options.db`. Populate with:

    python database/init_options_db.py
    python -m scripts_python.fetch_options --currency ETH
    python -m scripts_python.fetch_options --currency ETH --greeks

## Open all

    python -m jupyterlab analysis/option_notebook

## Notebooks that need --greeks

Only `08_greeks.ipynb` needs the `--greeks` flag when fetching.
All others work with the default chain snapshot.
"""


# ============================================================
# write everything
# ============================================================

NOTEBOOKS = {
    "01_chain_snapshot.ipynb": nb01,
    "02_iv_smile.ipynb": nb02,
    "03_iv_surface.ipynb": nb03,
    "04_put_call_ratio.ipynb": nb04,
    "05_skew_term.ipynb": nb05,
    "06_iv_vs_realized.ipynb": nb06,
    "07_max_pain.ipynb": nb07,
    "08_greeks.ipynb": nb08,
    "09_dashboard.ipynb": nb09,
}


def main():
    OPT.mkdir(parents=True, exist_ok=True)
    print(f"created: {OPT}")
    print()

    (OPT / "__init__.py").write_text("", encoding="utf-8")
    print("  wrote __init__.py")

    (OPT / "README.md").write_text(README, encoding="utf-8")
    print("  wrote README.md")

    for name, cells in NOTEBOOKS.items():
        path = OPT / name
        path.write_text(json.dumps(notebook(cells), indent=1), encoding="utf-8")
        md_n = sum(1 for c in cells if c["cell_type"] == "markdown")
        code_n = sum(1 for c in cells if c["cell_type"] == "code")
        print(f"  wrote {name:<32} md={md_n:>2} code={code_n:>2}")

    print()
    print("=" * 60)
    print("  done")
    print("=" * 60)
    print(f"  folder: {OPT}")
    print()
    print("  open with:")
    print("    python -m jupyterlab analysis/option_notebook")


if __name__ == "__main__":
    main()