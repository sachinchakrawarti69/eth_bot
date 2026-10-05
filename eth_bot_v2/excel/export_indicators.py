"""Export indicators-only view."""
from __future__ import annotations
from pathlib import Path
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference

from excel.common import style_header, autosize
from excel.export_ohlcv import load

ROOT    = Path(__file__).resolve().parents[1]
OUT     = ROOT / "exports" / "ETHUSDT_indicators.xlsx"


def build():
    df = load()
    wb = Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet("Indicators")
    ws.append(["Date","Close","SMA20","SMA50","SMA200",
               "EMA12","EMA26","RSI14","MACD","MACD_Hist","ATR14"])
    for d, row in df.iterrows():
        ws.append([d.date(),
                   float(row.close) if row.close == row.close else None,
                   float(row.sma_20) if row.sma_20 == row.sma_20 else None,
                   float(row.sma_50) if row.sma_50 == row.sma_50 else None,
                   None,
                   float(row.ema_12) if row.ema_12 == row.ema_12 else None,
                   float(row.ema_26) if row.ema_26 == row.ema_26 else None,
                   float(row.rsi_14) if row.rsi_14 == row.rsi_14 else None,
                   float(row["macd"]) if row["macd"] == row["macd"] else None,
                   float(row["macd_hist"]) if row["macd_hist"] == row["macd_hist"] else None,
                   None])
    style_header(ws)
    autosize(ws)
    chart = LineChart()
    chart.title = "ETHUSDT close + SMA50"
    chart.height = 8; chart.width = 22
    data = Reference(ws, min_col=2, max_col=4, min_row=1, max_row=ws.max_row)
    cats = Reference(ws, min_col=1, min_row=2, max_row=ws.max_row)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    ws.add_chart(chart, "M2")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"  wrote {OUT}")
    return OUT


if __name__ == "__main__":
    build()
