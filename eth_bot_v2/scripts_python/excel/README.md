# excel/

Excel export modules. One command runs everything.

## Command

    python -m excel.export_all

Writes timestamped files to `exports/`:

    exports/
    ├── ETHUSDT_ohlcv_20261005_1430.xlsx
    └── ETHUSDT_forecast_20261005_1430.xlsx

## Individual runs

    python -m excel.export_ohlcv
    python -m excel.export_forecasts

## Why timestamps

Files never collide. Excel can keep one open while the script writes the next.
