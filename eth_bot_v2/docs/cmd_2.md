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


python -m scripts_python.fetch_futures


python -m scripts_python.fetch_funding

python -m scripts_python.fetch_oi
python -m scripts_python.fetch_ls_ratio
python -m scripts_python.fetch_taker



python -m ml.predict --symbol ETHUSDT


python -m ml.predict --symbol BTCUSDT



python -m scripts_python.update_multi
python -m scripts_python.build_features
python -m ml.predict --symbol ETHUSDT
