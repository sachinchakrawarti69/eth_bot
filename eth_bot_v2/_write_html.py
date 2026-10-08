"""
Set up a separate ETH options database.

Creates:
  database/options.db
  database/schema/options/0001_option_chain.sql
  database/schema/options/0002_greeks.sql
  database/schema/options/0003_implied_volatility.sql
  database/schema/options/0004_option_summary.sql
  database/init_options_db.py
  scripts_python/fetch_options.py
  analysis/notebooks/11_options.ipynb

Run:
    python setup_options_db.py
Then:
    python database/init_options_db.py
    python -m scripts_python.fetch_options --currency ETH
"""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ============================================================
# 1. schema/options/*.sql
# ============================================================

SCHEMA_OPTION_CHAIN = """-- Raw option chain snapshots (per instrument).

CREATE TABLE IF NOT EXISTS option_chain (
    underlying    TEXT    NOT NULL,   -- 'ETH', 'BTC'
    expiry        INTEGER NOT NULL,   -- ms epoch of expiry
    strike        REAL    NOT NULL,
    kind          TEXT    NOT NULL,   -- 'C' or 'P'
    ts            INTEGER NOT NULL,   -- snapshot time (ms epoch)
    mark_price    REAL,
    bid           REAL,
    ask           REAL,
    bid_iv        REAL,
    ask_iv        REAL,
    mark_iv       REAL,
    oi            REAL,
    volume        REAL,
    underlying_px REAL,
    PRIMARY KEY (underlying, expiry, strike, kind, ts)
);

CREATE INDEX IF NOT EXISTS idx_chain_lookup
    ON option_chain (underlying, ts DESC);

CREATE INDEX IF NOT EXISTS idx_chain_expiry
    ON option_chain (underlying, expiry, ts DESC);
"""

SCHEMA_GREEKS = """-- Greeks per instrument snapshot.

CREATE TABLE IF NOT EXISTS greeks (
    underlying TEXT    NOT NULL,
    expiry     INTEGER NOT NULL,
    strike     REAL    NOT NULL,
    kind       TEXT    NOT NULL,
    ts         INTEGER NOT NULL,
    delta      REAL,
    gamma      REAL,
    theta      REAL,
    vega       REAL,
    rho        REAL,
    PRIMARY KEY (underlying, expiry, strike, kind, ts)
);

CREATE INDEX IF NOT EXISTS idx_greeks_lookup
    ON greeks (underlying, ts DESC);
"""

SCHEMA_IV = """-- Implied volatility surface.

CREATE TABLE IF NOT EXISTS implied_volatility (
    underlying TEXT    NOT NULL,
    expiry     INTEGER NOT NULL,
    strike     REAL    NOT NULL,
    kind       TEXT    NOT NULL,
    ts         INTEGER NOT NULL,
    iv         REAL    NOT NULL,
    iv_fit     REAL,
    moneyness  REAL,
    dte        REAL,
    PRIMARY KEY (underlying, expiry, strike, kind, ts)
);

CREATE INDEX IF NOT EXISTS idx_iv_lookup
    ON implied_volatility (underlying, ts DESC);
"""

SCHEMA_SUMMARY = """-- Aggregated options metrics (one row per underlying per hour).

CREATE TABLE IF NOT EXISTS option_summary (
    underlying     TEXT    NOT NULL,
    ts             INTEGER NOT NULL,
    total_oi_call  REAL,
    total_oi_put   REAL,
    pcr_oi         REAL,
    total_vol_call REAL,
    total_vol_put  REAL,
    pcr_vol        REAL,
    atm_iv         REAL,
    iv_25d_skew    REAL,
    term_structure REAL,
    max_pain       REAL,
    PRIMARY KEY (underlying, ts)
);

CREATE INDEX IF NOT EXISTS idx_summary_lookup
    ON option_summary (underlying, ts DESC);
"""

# ============================================================
# 2. database/init_options_db.py
# ============================================================

INIT_OPTIONS = '''"""Apply every SQL file in database/schema/options/ to options.db."""

import sqlite3
import sys
import time
from pathlib import Path

DB_PATH    = Path(__file__).resolve().parent / "options.db"
SCHEMA_DIR = Path(__file__).resolve().parent / "schema" / "options"


def init() -> int:
    if not SCHEMA_DIR.exists():
        print(f"schema dir missing: {SCHEMA_DIR}")
        return 1

    files = sorted(SCHEMA_DIR.glob("*.sql"))
    if not files:
        print(f"no .sql files in {SCHEMA_DIR}")
        return 1

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _schema_version ("
            "  filename   TEXT PRIMARY KEY,"
            "  applied_at INTEGER NOT NULL)"
        )
        conn.commit()

        for f in files:
            print(f"applying {f.name}")
            conn.executescript(f.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT OR IGNORE INTO _schema_version (filename, applied_at) "
                "VALUES (?, ?)", (f.name, int(time.time())))
            conn.commit()

        print(f"\\ntables in {DB_PATH.name}:")
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for t in tables:
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:<22} rows={n}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(init())
'''

# ============================================================
# 3. scripts_python/fetch_options.py
# ============================================================

FETCH_OPTIONS = '''"""Fetch ETH/BTC options data from Deribit into options.db.

Usage:
    python -m scripts_python.fetch_options
    python -m scripts_python.fetch_options --currency ETH
    python -m scripts_python.fetch_options --currency ETH,BTC
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "options.db"

DERIBIT = "https://www.deribit.com/api/v2"


def req(path: str, params: dict | None = None) -> dict:
    url = f"{DERIBIT}{path}"
    r = requests.get(url, params=params or {}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result", data)


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def parse_instrument(name: str):
    parts = name.split("-")
    if len(parts) != 4:
        return None
    underlying, expiry_str, strike_str, kind = parts
    try:
        expiry_dt = datetime.strptime(expiry_str, "%d%b%y").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    try:
        strike = float(strike_str)
    except ValueError:
        return None
    return {
        "underlying": underlying,
        "expiry":     int(expiry_dt.timestamp() * 1000),
        "strike":     strike,
        "kind":       kind,
    }


def upsert_chain(conn, ts, rows):
    conn.executemany(
        """INSERT INTO option_chain
           (underlying, expiry, strike, kind, ts,
            mark_price, bid, ask, bid_iv, ask_iv, mark_iv,
            oi, volume, underlying_px)
           VALUES (?,?,?,?,?, ?,?,?,?,?,?, ?,?,?)
           ON CONFLICT(underlying, expiry, strike, kind, ts) DO UPDATE SET
             mark_price=excluded.mark_price, bid=excluded.bid, ask=excluded.ask,
             bid_iv=excluded.bid_iv, ask_iv=excluded.ask_iv,
             mark_iv=excluded.mark_iv, oi=excluded.oi,
             volume=excluded.volume, underlying_px=excluded.underlying_px""",
        rows)
    conn.commit()


def upsert_iv(conn, ts, rows):
    conn.executemany(
        """INSERT INTO implied_volatility
           (underlying, expiry, strike, kind, ts, iv, iv_fit, moneyness, dte)
           VALUES (?,?,?,?,?, ?,?,?,?)
           ON CONFLICT(underlying, expiry, strike, kind, ts) DO UPDATE SET
             iv=excluded.iv, iv_fit=excluded.iv_fit,
             moneyness=excluded.moneyness, dte=excluded.dte""",
        rows)
    conn.commit()


def upsert_summary(conn, row):
    conn.execute(
        """INSERT INTO option_summary
           (underlying, ts, total_oi_call, total_oi_put, pcr_oi,
            total_vol_call, total_vol_put, pcr_vol,
            atm_iv, iv_25d_skew, term_structure, max_pain)
           VALUES (?,?,?,?,?, ?,?,?, ?,?,?,?)
           ON CONFLICT(underlying, ts) DO UPDATE SET
             total_oi_call=excluded.total_oi_call,
             total_oi_put=excluded.total_oi_put,
             pcr_oi=excluded.pcr_oi,
             total_vol_call=excluded.total_vol_call,
             total_vol_put=excluded.total_vol_put,
             pcr_vol=excluded.pcr_vol,
             atm_iv=excluded.atm_iv,
             iv_25d_skew=excluded.iv_25d_skew,
             term_structure=excluded.term_structure,
             max_pain=excluded.max_pain""",
        row)
    conn.commit()


def compute_summary(underlying, ts, snapshot):
    total_oi_call = total_oi_put = 0.0
    total_vol_call = total_vol_put = 0.0
    oi_by_strike = {}

    for s in snapshot:
        info = parse_instrument(s.get("instrument_name", ""))
        if not info:
            continue

        oi = float(s.get("open_interest") or 0)
        vol = float(s.get("volume") or 0)

        if info["kind"] == "C":
            total_oi_call += oi
            total_vol_call += vol
        else:
            total_oi_put += oi
            total_vol_put += vol

        oi_by_strike[info["strike"]] = oi_by_strike.get(info["strike"], 0) + oi

    pcr_oi  = (total_oi_put / total_oi_call) if total_oi_call else None
    pcr_vol = (total_vol_put / total_vol_call) if total_vol_call else None
    max_pain = max(oi_by_strike, key=oi_by_strike.get) if oi_by_strike else None

    return (underlying, ts,
            total_oi_call, total_oi_put, pcr_oi,
            total_vol_call, total_vol_put, pcr_vol,
            None, None, None, max_pain)


def fetch_currency(conn, currency):
    print(f"[{currency}]")
    print(f"  calling Deribit...")

    try:
        snapshot = req("/public/get_book_summary_by_currency",
                       {"currency": currency, "kind": "option"})
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        return 0

    if not snapshot:
        print(f"  no instruments returned")
        return 0

    print(f"  {len(snapshot)} instruments")
    ts = now_ms()

    chain_rows = []
    iv_rows = []

    for s in snapshot:
        info = parse_instrument(s.get("instrument_name", ""))
        if not info:
            continue

        underlying_px = s.get("underlying_price")
        underlying_px = float(underlying_px) if underlying_px else None

        mark_iv = s.get("mark_iv")
        mark_iv = float(mark_iv) / 100.0 if mark_iv is not None else None
        bid_iv = s.get("bid_iv")
        bid_iv = float(bid_iv) / 100.0 if bid_iv is not None else None
        ask_iv = s.get("ask_iv")
        ask_iv = float(ask_iv) / 100.0 if ask_iv is not None else None

        chain_rows.append((
            info["underlying"], info["expiry"], info["strike"], info["kind"], ts,
            float(s.get("mark_price") or 0),
            float(s.get("bid_price") or 0),
            float(s.get("ask_price") or 0),
            bid_iv, ask_iv, mark_iv,
            float(s.get("open_interest") or 0),
            float(s.get("volume") or 0),
            underlying_px,
        ))

        moneyness = info["strike"] / underlying_px if underlying_px else None
        dte = (info["expiry"] - ts) / 86_400_000.0 if info["expiry"] else None

        if mark_iv is not None:
            iv_rows.append((
                info["underlying"], info["expiry"], info["strike"], info["kind"], ts,
                mark_iv, None, moneyness, dte,
            ))

    upsert_chain(conn, ts, chain_rows)
    print(f"  option_chain          +{len(chain_rows)} rows")

    if iv_rows:
        upsert_iv(conn, ts, iv_rows)
        print(f"  implied_volatility    +{len(iv_rows)} rows")

    summary = compute_summary(currency, ts, snapshot)
    upsert_summary(conn, summary)
    print(f"  option_summary        +1 row")
    print(f"    pcr_oi   = {summary[4]}")
    print(f"    max_pain = {summary[11]}")

    return len(chain_rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--currency", type=str, default="ETH")
    args = ap.parse_args()
    currencies = [c.strip().upper() for c in args.currency.split(",") if c.strip()]

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        print("Run: python database/init_options_db.py")
        return 1

    print("=" * 60)
    print("  FETCH OPTIONS  ->  options.db")
    print("=" * 60)
    print(f"  currencies: {', '.join(currencies)}")
    print()

    conn = sqlite3.connect(DB_PATH)
    try:
        for cur in currencies:
            try:
                fetch_currency(conn, cur)
            except Exception as e:
                print(f"  {cur} FAIL: {type(e).__name__}: {e}")
            print()

        print("=" * 60)
        print("  TABLE COUNTS  (options.db)")
        print("=" * 60)
        for t in ("option_chain", "greeks", "implied_volatility", "option_summary"):
            try:
                n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"  {t:<22} {n:>7}")
            except Exception as e:
                print(f"  {t:<22} ERROR: {e}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
'''

# ============================================================
# 4. analysis/notebooks/11_options.ipynb
# ============================================================

def make_notebook():
    def md(t):
        return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}
    def code(s):
        return {"cell_type": "code", "execution_count": None, "metadata": {},
                "outputs": [], "source": s.splitlines(keepends=True)}

    cells = []

    cells.append(md("""# 11 - ETH Options (separate DB)

Options data lives in `database/options.db`, not `market.db`.

Covers:

1. Load option_chain
2. IV smile (one expiry)
3. IV surface (strike × expiry)
4. Put/call ratio over time
5. ATM IV vs realized vol
6. Skew & term structure
7. Summary dashboard
"""))

    cells.append(md("## Setup"))

    cells.append(code('''import sys, sqlite3
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_p = Path.cwd().resolve()
while _p != _p.parent and not (_p / "database").exists():
    _p = _p.parent
sys.path.insert(0, str(_p))

OPT_DB  = _p / "database" / "options.db"
MKT_DB  = _p / "database" / "market.db"

pd.set_option("display.width", 180)
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
print("market.db :", MKT_DB)'''))

    cells.append(md("## 1. Load option chain"))

    cells.append(code('''oc = opt("SELECT * FROM option_chain ORDER BY ts DESC, expiry, strike")
print("rows:", len(oc))
if not oc.empty:
    print("range:", pd.to_datetime(oc.ts.min(), unit="ms"), "->",
          pd.to_datetime(oc.ts.max(), unit="ms"))
    print("snapshots:", oc.ts.nunique())
    print("expiries :", oc.expiry.nunique())
oc.head()'''))

    cells.append(md("## 2. IV smile — nearest expiry"))

    cells.append(code('''if not oc.empty:
    oc["dte"] = (oc.expiry - oc.ts) / 86_400_000.0
    valid = oc[(oc.dte > 2) & (oc.dte < 60) & oc.mark_iv.notna()]
    if not valid.empty:
        target = valid.expiry.value_counts().index[0]
        snap = valid[valid.expiry == target]
        latest = snap[snap.ts == snap.ts.max()]

        fig, ax = plt.subplots()
        for kind, color in [("C", "seagreen"), ("P", "crimson")]:
            s = latest[latest["kind"] == kind].sort_values("strike")
            ax.plot(s.strike, s.mark_iv * 100, "o-", color=color,
                    label="Calls" if kind == "C" else "Puts")
        ax.set_title(f"IV smile — {pd.to_datetime(target, unit='ms').date()}")
        ax.set_xlabel("strike")
        ax.set_ylabel("IV %")
        ax.legend()
        plt.tight_layout()
        plt.show()
    else:
        print("no snapshots yet")'''))

    cells.append(md("## 3. IV surface — strike × expiry"))

    cells.append(code('''if not oc.empty and "dte" in oc.columns:
    surf = oc[oc.mark_iv.notna()].copy()
    surf = surf[(surf.dte > 0) & (surf.dte < 120)]
    if not surf.empty:
        latest_ts = surf.ts.max()
        snap = surf[surf.ts == latest_ts]
        pivot = snap.pivot_table(index="expiry", columns="strike",
                                 values="mark_iv", aggfunc="mean")
        if not pivot.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.imshow(pivot.values * 100, aspect="auto", cmap="viridis")
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels([pd.to_datetime(e, unit="ms").date() for e in pivot.index])
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels([f"{int(s)}" for s in pivot.columns], rotation=45)
            plt.colorbar(im, ax=ax, label="IV %")
            ax.set_title("IV surface")
            ax.set_xlabel("strike")
            ax.set_ylabel("expiry")
            plt.tight_layout()
            plt.show()'''))

    cells.append(md("## 4. Put/call ratio over time"))

    cells.append(code('''sm = opt("SELECT * FROM option_summary WHERE underlying='ETH' ORDER BY ts")
if not sm.empty:
    sm["date"] = pd.to_datetime(sm.ts, unit="ms")
    sm = sm.set_index("date")

    fig, ax = plt.subplots()
    ax.plot(sm.index, sm.pcr_oi, label="PCR (OI)", color="steelblue")
    ax.axhline(1.0, ls="--", color="gray", lw=0.8)
    ax.set_title("ETH put/call ratio (OI)")
    ax.legend()
    plt.tight_layout()
    plt.show()
    print(sm[["pcr_oi", "pcr_vol"]].tail())
else:
    print("no summary rows yet")'''))

    cells.append(md("## 5. ATM IV vs realized vol"))

    cells.append(code('''if not sm.empty:
    px = mkt("SELECT open_time, close FROM ohlcv WHERE symbol='ETHUSDT' AND timeframe='1d' ORDER BY open_time")
    px["date"] = pd.to_datetime(px.open_time, unit="ms")
    px = px.set_index("date")["close"]
    rv = px.pct_change().rolling(30).std() * np.sqrt(365)

    fig, ax = plt.subplots()
    if sm.atm_iv.notna().any():
        ax.plot(sm.index, sm.atm_iv * 100, label="ATM IV", color="crimson")
    ax.plot(rv.index, rv * 100, label="30d realized vol", color="steelblue")
    ax.set_title("vol comparison")
    ax.legend()
    plt.tight_layout()
    plt.show()'''))

    cells.append(md("## 6. Summary dashboard"))

    cells.append(code('''if not sm.empty:
    last = sm.iloc[-1]
    print("=" * 50)
    print("  ETH OPTIONS SNAPSHOT")
    print("=" * 50)
    print(f"  as of     : {last.name}")
    print(f"  PCR (OI)  : {last.pcr_oi}")
    print(f"  PCR (vol) : {last.pcr_vol}")
    print(f"  max pain  : {last.max_pain}")
    print("=" * 50)'''))

    cells.append(md("""## Next steps

- Fetch hourly: `python -m scripts_python.fetch_options --currency ETH`
- Add to scheduler
- Merge into RL features later by joining on `ts`
"""))

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }


# ============================================================
# write everything
# ============================================================

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def main():
    print("=" * 60)
    print("  SETUP OPTIONS DB")
    print("=" * 60)
    print()

    # 1. schema files
    write(ROOT / "database" / "schema" / "options" / "0001_option_chain.sql",
          SCHEMA_OPTION_CHAIN)
    write(ROOT / "database" / "schema" / "options" / "0002_greeks.sql",
          SCHEMA_GREEKS)
    write(ROOT / "database" / "schema" / "options" / "0003_implied_volatility.sql",
          SCHEMA_IV)
    write(ROOT / "database" / "schema" / "options" / "0004_option_summary.sql",
          SCHEMA_SUMMARY)

    # 2. init script
    write(ROOT / "database" / "init_options_db.py", INIT_OPTIONS)

    # 3. fetcher
    write(ROOT / "scripts_python" / "fetch_options.py", FETCH_OPTIONS)

    # 4. notebook
    nb = make_notebook()
    nb_path = ROOT / "analysis" / "notebooks" / "11_options.ipynb"
    nb_path.parent.mkdir(parents=True, exist_ok=True)
    nb_path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"  wrote {nb_path.relative_to(ROOT)}")

    print()
    print("=" * 60)
    print("  NEXT STEPS")
    print("=" * 60)
    print()
    print("  1. create options.db:")
    print("       python database/init_options_db.py")
    print()
    print("  2. fetch options data:")
    print("       python -m scripts_python.fetch_options --currency ETH")
    print()
    print("  3. open the notebook:")
    print("       python -m jupyterlab analysis/notebooks/11_options.ipynb")
    print()


if __name__ == "__main__":
    main()