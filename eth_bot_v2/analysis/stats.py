"""Return / volatility / drawdown summaries."""
import numpy as np
import pandas as pd


def summary(close: pd.Series) -> dict:
    r = close.pct_change().dropna()
    cum = (1 + r).cumprod()
    dd = (cum / cum.cummax() - 1).min()
    return {
        "start":        close.index[0].date().isoformat(),
        "end":          close.index[-1].date().isoformat(),
        "days":         int(len(close)),
        "total_return": float(cum.iloc[-1] - 1),
        "ann_vol":      float(r.std(ddof=0) * np.sqrt(365)),
        "sharpe":       float(r.mean() / r.std(ddof=0) * np.sqrt(365)),
        "max_drawdown": float(dd),
        "best_day":     float(r.max()),
        "worst_day":    float(r.min()),
    }
