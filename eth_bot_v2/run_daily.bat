@echo off
cd /d "%~dp0"

echo ==== UPDATE DATA ====
python -m scripts_python.fetchers.multi
python -m scripts_python.fetchers.futures
python -m scripts_python.fetchers.funding

echo.
echo ==== BUILD FEATURES ====
python -m scripts_python.builders.features

echo.
echo ==== TRADE SIGNAL ====
python -m trader.run

echo.
pause
