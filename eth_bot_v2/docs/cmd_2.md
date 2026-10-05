python -m excel.export_all

python -m scripts_python.update_market  
python -m excel.export_all  
python -m reports.daily_report

python -m run

python -m venv .venv
.\.venv\Scripts\Activate.ps1
