python -m excel.export_all

python -m scripts_python.update_market  
python -m excel.export_all  
python -m reports.daily_report

python -m run

python -m venv .venv
.\.venv\Scripts\Activate.ps1




python -m scripts_python.fetch_options --currency ETH


python -m scripts_python.export_options --currency ETH


python -m scripts_python.export_options --currency BTC

python -m scripts_python.export_options --currency ETH,BTC


python -m scripts_python.gui.take_trade