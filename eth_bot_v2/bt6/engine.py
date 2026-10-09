"""Backtest engine with realistic fees."""

from __future__ import annotations
import numpy as np
import pandas as pd


ROUND_TRIP_FEE = 0.0010   # 0.10% per side, taker


def simulate(df, strategy):
    """Return list of trades for a given strategy."""
    entry_mask = strategy["entry"](df)
    direction  = strategy["direction"]
    hold       = strategy["hold_days"]
    mult       = 1 if direction == "long" else -1

    trades = []
    i = 0
    n = len(df)
    while i < n:
        if bool(entry_mask.iloc[i]):
            entry_price = float(df["close"].iloc[i])
            entry_date  = df.index[i]
            exit_idx    = i + hold
            if exit_idx >= n:
                break
            exit_price  = float(df["close"].iloc[exit_idx])
            exit_date   = df.index[exit_idx]

            gross = (exit_price / entry_price - 1) * mult
            net   = gross - ROUND_TRIP_FEE

            trades.append({
                "entry_date":  entry_date,
                "exit_date":   exit_date,
                "entry_price": entry_price,
                "exit_price":  exit_price,
                "return_gross": gross,
                "return_net":   net,
                "direction":   direction,
            })
            i += 1     # no overlapping trades
        else:
            i += 1
    return trades


def metrics(trades):
    if not trades:
        return None
    t = pd.DataFrame(trades)
    n = len(t)
    wins = t[t["return_net"] > 0]
    losses = t[t["return_net"] <= 0]

    hit = len(wins) / n
    avg_win = float(wins["return_net"].mean()) if len(wins) else 0.0
    avg_loss = float(losses["return_net"].mean()) if len(losses) else 0.0
    exp = hit * avg_win + (1 - hit) * avg_loss

    cum = (1 + t["return_net"]).cumprod()
    total = float(cum.iloc[-1] - 1) if len(cum) else 0.0
    dd = float((cum / cum.cummax() - 1).min()) if len(cum) else 0.0

    # Sharpe per trade, annualized by trades/year
    t["entry_year"] = pd.to_datetime(t["entry_date"]).dt.year
    years = t["entry_year"].nunique() or 1
    tpy = n / years
    vol = t["return_net"].std(ddof=0)
    sharpe = float(exp / vol * np.sqrt(tpy)) if vol > 0 else 0.0

    gw = float(wins["return_net"].sum()) if len(wins) else 0.0
    gl = abs(float(losses["return_net"].sum())) if len(losses) else 0.0
    pf = gw / gl if gl > 0 else float("inf")

    # per-year
    by_year = []
    for y, g in t.groupby("entry_year"):
        w = g[g["return_net"] > 0]
        l = g[g["return_net"] <= 0]
        hr = len(w) / len(g)
        aw = float(w["return_net"].mean()) if len(w) else 0.0
        al = float(l["return_net"].mean()) if len(l) else 0.0
        e = hr * aw + (1 - hr) * al
        cum_year = float((1 + g["return_net"]).prod() - 1)
        by_year.append({
            "year": int(y),
            "n": len(g),
            "hit": hr,
            "expectancy": e,
            "total_return": cum_year,
        })

    pos_years = sum(1 for y in by_year if y["total_return"] > 0)

    return {
        "n": n,
        "hit_rate": hit,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": exp,
        "total_return": total,
        "max_dd": dd,
        "sharpe": sharpe,
        "profit_factor": pf if pf != float("inf") else 999.0,
        "by_year": by_year,
        "pos_years": pos_years,
        "total_years": len(by_year),
        "trades_df": t,
    }


def verdict(m):
    if m is None: return "no trades"
    if m["n"] < 10: return "too few"
    if m["expectancy"] > 0.005 and m["sharpe"] > 0.8 and m["pos_years"] >= m["total_years"] * 0.6:
        return "strong"
    if m["expectancy"] > 0.001 and m["sharpe"] > 0.3:
        return "edge"
    if m["expectancy"] > 0:
        return "weak"
    return "none"
