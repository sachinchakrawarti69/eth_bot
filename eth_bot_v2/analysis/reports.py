"""Write reports/daily/YYYY-MM-DD/summary.md"""
import json
from datetime import date
from pathlib import Path

from analysis.loader import load_ohlcv
from analysis.indicators import add_all
from analysis import stats

OUT = Path(__file__).resolve().parents[1] / "reports" / "daily"


def build() -> None:
    today = date.today().isoformat()
    d = OUT / today
    d.mkdir(parents=True, exist_ok=True)

    df = add_all(load_ohlcv())
    s  = stats.summary(df.close)
    last = df.iloc[-1]

    lines = [
        f"# ETHUSDT 1d - {today}",
        "",
        "## Summary",
        *[f"- **{k}**: {v}" for k, v in s.items()],
        "",
        "## Latest",
        f"- close   : {last.close:.2f}",
        f"- sma_50  : {last.sma_50:.2f}",
        f"- sma_200 : {last.sma_200:.2f}",
        f"- rsi_14  : {last.rsi_14:.2f}",
        f"- atr_14  : {last.atr_14:.2f}",
    ]
    (d / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    (d / "summary.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    print(f"wrote {d}")


if __name__ == "__main__":
    build()
