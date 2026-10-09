"""Position sizing for realistic backtests."""

import numpy as np
import pandas as pd


def equity_curve(trades, risk_pct=2.0, max_leverage=1.0):
    """Return equity curve if you risk `risk_pct` of capital per trade.

    risk_pct: percent of current equity to risk per trade (e.g. 2.0 = 2%)
    max_leverage: cap on position size vs account (default 1.0 = no leverage)

    Simplified model: each trade loses/gains `return_net * position_size`
    where position_size is fixed at risk_pct / stop_distance equivalent.
    Since we don't have stop distances in this backtest, we approximate
    position size = risk_pct / typical_loss.
    """
    if not trades:
        return pd.Series(dtype=float)

    t = pd.DataFrame(trades)
    r = t["return_net"].values

    # approximate: size each trade so a typical loss = risk_pct
    typical_loss = abs(np.percentile(r[r < 0], 50)) if (r < 0).any() else 0.05
    if typical_loss < 0.001:
        typical_loss = 0.05
    pos_size = min(risk_pct / 100 / typical_loss, max_leverage)

    # equity compounding
    equity = [1.0]
    for ri in r:
        equity.append(equity[-1] * (1 + ri * pos_size))

    dates = pd.to_datetime(t["exit_date"]).tolist()
    dates = [pd.to_datetime(t["entry_date"]).iloc[0]] + dates
    return pd.Series(equity[1:], index=dates)


def summary(trades, risk_pct=2.0):
    """Full metrics with position sizing applied."""
    if not trades:
        return None

    eq = equity_curve(trades, risk_pct)
    t = pd.DataFrame(trades)
    r = t["return_net"].values

    total = float(eq.iloc[-1] - 1) if len(eq) else 0.0
    peak = eq.cummax()
    dd = float((eq / peak - 1).min()) if len(eq) else 0.0
    vol = np.std(np.diff(np.log(eq))) if len(eq) > 1 else 0.0
    n_years = (eq.index[-1] - eq.index[0]).days / 365 if len(eq) else 1
    cagr = (eq.iloc[-1]) ** (1 / max(n_years, 0.1)) - 1 if len(eq) else 0.0
    sharpe = (np.mean(np.diff(np.log(eq))) / vol * np.sqrt(252)
              if vol > 0 else 0.0)

    return {
        "total_return": total,
        "cagr":         float(cagr),
        "max_dd":       dd,
        "sharpe":       float(sharpe),
        "n":            len(t),
        "risk_pct":     risk_pct,
    }