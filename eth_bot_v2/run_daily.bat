@echo off
cd /d "%~dp0"

echo ==== UPDATE DATA ====
python -m scripts_python.update_multi
python -m scripts_python.fetch_futures
python -m scripts_python.fetch_funding

echo.
echo ==== BUILD FEATURES ====
python -m scripts_python.build_features

echo.
echo ==== TRADE SIGNAL ====
python -m trader.run

echo.
pause
