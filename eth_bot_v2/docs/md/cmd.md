# Command Reference

Every command for `eth_bot_v2`. Copy-paste from here.

Run from project root:

```powershell
cd "D:\Sachin Chakrawarti\Learn\done\eth_bot\eth_bot_v2"
```

---

## 1. First-time setup

```powershell
# install dependencies
python -m pip install --upgrade pip
python -m pip install requests pandas numpy matplotlib scikit-learn openpyxl jinja2 flask flask-cors plyer

# create databases
python database\init_db.py
python database\init_options_db.py
```

---

## 2. Fetch data

### Multi-symbol OHLCV

```powershell
python -m scripts_python.update_multi
```

Adds BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT at 1d and 1h.

Custom:

```powershell
python -m scripts_python.update_multi --symbols BTCUSDT,ETHUSDT
python -m scripts_python.update_multi --timeframes 1h
python -m scripts_python.update_multi --symbols BTCUSDT --timeframes 1h,4h,1d
```

### Futures OHLCV

```powershell
python -m scripts_python.fetch_futures
```

### Funding rate

```powershell
python -m scripts_python.fetch_funding
python -m scripts_python.fetch_funding --symbols ETHUSDT
```

### Open interest

```powershell
python -m scripts_python.fetch_oi
```

### Long/short ratio

```powershell
python -m scripts_python.fetch_ls_ratio
```

### Taker volume

```powershell
python -m scripts_python.fetch_taker
```

### Options (Deribit)

```powershell
python -m scripts_python.fetch_options --currency ETH
python -m scripts_python.fetch_options --currency ETH,BTC
python -m scripts_python.fetch_options --currency ETH --greeks
```

---

## 3. Build features and levels

### Features table

```powershell
python -m scripts_python.build_features
```

Rebuild from scratch:

```powershell
python -m scripts_python.build_features --full
```

### Support/resistance

```powershell
python -m scripts_python.compute_sr
```

Custom:

```powershell
python -m scripts_python.compute_sr --symbols ETHUSDT
python -m scripts_python.compute_sr --timeframes 1h,4h,1d
```

---

## 4. Analysis

### Statistical mode

```powershell
python -m scripts_python.statistical_mode
```

Output: ranking of 60 signals × 3 horizons.

### Backtest

```powershell
python -m scripts_python.backtest --list
python -m scripts_python.backtest --strategy mean_reversion
python -m scripts_python.backtest
```

### Daily report

```powershell
python -m reports_pkg.daily_report
```

Writes `reports/daily/YYYY-MM-DD/summary.md`.

---

## 5. Trade setups

```powershell
python -m scripts_python.opportunity
```

Custom:

```powershell
python -m scripts_python.opportunity --account 5000 --risk 0.5
python -m scripts_python.opportunity --symbols ETHUSDT
```

Writes to `trade_setups` and `reports/orders/YYYY-MM-DD.json`.

---

## 6. Web UI

### Start server

```powershell
python scripts_python\web\api.py
```

Open in browser:

```
http://localhost:8000
```

Network URL (for phone):

```powershell
ipconfig | findstr /C:"IPv4"
```

Then `http://<your-ip>:8000`.

Stop with `Ctrl+C`.

---

## 7. Terminal UIs

### Compact trade desk

```powershell
python -m scripts_python.cmd.take_trade
```

### Desktop window

```powershell
python -m scripts_python.gui.take_trade
```

---

## 8. Excel export

```powershell
python -m excel.export_all
```

Individual:

```powershell
python -m excel.export_ohlcv
python -m excel.export_forecasts
python -m excel.export_multi
```

Files go to `exports/`.

---

## 9. Jupyter

```powershell
python -m jupyterlab
```

Open specific notebook:

```powershell
python -m jupyterlab analysis\notebooks\01_ohlcv.ipynb
```

Notebook folders:

| Folder | Purpose |
|---|---|
| `analysis/notebooks/` | Exploratory |
| `analysis/prediction_notebooks/` | Baseline, linear, trees, LSTM |
| `analysis/forecast_notebooks/` | Next candle/day/week |
| `analysis/option_notebook/` | Options analysis |
| `analysis/eth_current_prediction/` | Live prediction dashboards |

---

## 10. Auto-commit + push

### Init config

```powershell
python git_auto_push.py --init-config
```

Writes `.git_auto_push.json`.

### Test notification

```powershell
python -c "from git_auto_push import Notifier, load_config; n=Notifier(load_config()); n.toast('Test', 'ok'); n.beep()"
```

### Run watcher

```powershell
python git_auto_push.py
python git_auto_push.py --no-push
python git_auto_push.py --dry-run
python git_auto_push.py --once
python git_auto_push.py --interval 15
python git_auto_push.py --notify-push
python git_auto_push.py --no-notify
```

### Preview commit message

```powershell
python commit_messages.py
python commit_messages.py --subject
python commit_messages.py --json
python commit_messages.py --test
```

---

## 11. Database

### Inspect

```powershell
python database\show.py
python database\show.py ohlcv
python database\show.py features
python database\show.py trade_setups
```

### Raw sqlite

```powershell
sqlite3 database\market.db ".tables"
sqlite3 database\market.db ".schema ohlcv"
sqlite3 database\market.db "SELECT COUNT(*) FROM ohlcv;"
sqlite3 database\market.db "SELECT symbol, timeframe, COUNT(*) FROM ohlcv GROUP BY symbol, timeframe;"
```

### Backup

```powershell
Copy-Item database\market.db database\market.db.bak -Force
```

Safe backup (no lock conflicts):

```powershell
python -c "import sqlite3; sqlite3.connect('database/market.db').execute(\"VACUUM INTO 'database/backup.db'\")"
```

### Vacuum

```powershell
python -c "import sqlite3; c=sqlite3.connect('database/market.db'); c.execute('VACUUM'); c.close(); print('vacuumed')"
```

---

## 12. Verification

### All tables

```powershell
python -c "import sqlite3; c=sqlite3.connect('database/market.db'); [print(r) for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name\")]"
```

### OHLCV counts

```powershell
python -c "import sqlite3; c=sqlite3.connect('database/market.db'); [print(r) for r in c.execute(\"SELECT symbol, timeframe, COUNT(*) FROM ohlcv GROUP BY symbol, timeframe ORDER BY symbol, timeframe\")]"
```

### Features

```powershell
python -c "import sqlite3; c=sqlite3.connect('database/market.db'); print('features:', c.execute('SELECT COUNT(*) FROM features').fetchone()[0])"
```

### S/R levels

```powershell
python -c "import sqlite3; c=sqlite3.connect('database/market.db'); [print(r) for r in c.execute(\"SELECT source, COUNT(*) FROM sr_levels GROUP BY source\")]"
```

### Signal stats

```powershell
python -c "import sqlite3; c=sqlite3.connect('database/market.db'); [print(r) for r in c.execute(\"SELECT verdict, COUNT(*) FROM signal_stats GROUP BY verdict ORDER BY COUNT(*) DESC\")]"
```

### Today's setups

```powershell
python -c "import sqlite3; c=sqlite3.connect('database/market.db'); [print(r) for r in c.execute(\"SELECT symbol, strategy, direction, entry, stop, target FROM trade_setups ORDER BY date DESC, confidence DESC LIMIT 10\")]"
```

### Backtest results

```powershell
python -c "import sqlite3; c=sqlite3.connect('database/market.db'); [print(r) for r in c.execute(\"SELECT name, n_trades, ROUND(expectancy*100,3), ROUND(sharpe,2), verdict FROM backtest_runs ORDER BY expectancy DESC\")]"
```

---

## 13. Git (manual)

```powershell
git status
git add -A
git commit -m "message"
git push
git pull
git log --oneline -10
```

Undo last commit (keep changes):

```powershell
git reset --soft HEAD~1
```

Discard local changes:

```powershell
git checkout -- <file>
git reset --hard HEAD
```

---

## 14. Daily workflow

```powershell
cd "D:\Sachin Chakrawarti\Learn\done\eth_bot\eth_bot_v2"

# 1. refresh data
python -m scripts_python.fetch_futures
python -m scripts_python.fetch_funding
python -m scripts_python.fetch_oi
python -m scripts_python.fetch_ls_ratio
python -m scripts_python.fetch_taker
python -m scripts_python.fetch_options --currency ETH,BTC

# 2. rebuild features + levels
python -m scripts_python.build_features
python -m scripts_python.compute_sr

# 3. generate today's setups
python -m scripts_python.opportunity

# 4. view in browser
python scripts_python\web\api.py
```

Total time: ~3 minutes.

---

## 15. Automation

### Daily update at 00:05 UTC

```powershell
$action  = New-ScheduledTaskAction -Execute "python" `
  -Argument "-m scripts_python.fetch_futures"
$trigger = New-ScheduledTaskTrigger -Daily -At "00:05"
Register-ScheduledTask -TaskName "ethbot_futures" `
  -Action $action -Trigger $trigger -Force
```

### Hourly options fetch

```powershell
$action  = New-ScheduledTaskAction -Execute "python" `
  -Argument "-m scripts_python.fetch_options --currency ETH,BTC"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "ethbot_options" `
  -Action $action -Trigger $trigger -Force
```

### Remove a task

```powershell
Unregister-ScheduledTask -TaskName "ethbot_futures" -Confirm:$false
```

### List tasks

```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like "ethbot_*" }
```

---

## 16. Clean up

### Clear Python caches

```powershell
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter .ipynb_checkpoints | Remove-Item -Recurse -Force
```

### Clear old Excel exports

```powershell
Get-ChildItem exports\*.xlsx |
  Sort-Object LastWriteTime -Descending |
  Select-Object -Skip 5 |
  Remove-Item -Force
```

### Clear old reports

```powershell
Get-ChildItem reports\daily -Directory |
  Sort-Object Name -Descending |
  Select-Object -Skip 30 |
  Remove-Item -Recurse -Force
```

---

## 17. Rebuild from scratch

**Careful — deletes all data.**

```powershell
Remove-Item database\market.db
Remove-Item database\options.db

python database\init_db.py
python database\init_options_db.py

python -m scripts_python.update_multi
python -m scripts_python.fetch_futures
python -m scripts_python.fetch_funding
python -m scripts_python.fetch_oi
python -m scripts_python.fetch_ls_ratio
python -m scripts_python.fetch_taker
python -m scripts_python.fetch_options --currency ETH,BTC

python -m scripts_python.build_features
python -m scripts_python.compute_sr
python -m scripts_python.statistical_mode
python -m scripts_python.backtest
python -m scripts_python.opportunity
```

---

## 18. Troubleshooting

### `ModuleNotFoundError: No module named 'xxx'`

```powershell
python -m pip install xxx
```

Common:

```powershell
python -m pip install requests pandas numpy matplotlib scikit-learn openpyxl jinja2 flask flask-cors plyer
```

### `no such table: xxx`

```powershell
python database\init_db.py
python database\init_options_db.py
```

### `database is locked`

Close other Python/Jupyter processes:

```powershell
Get-Process python, pythonw | Stop-Process -Force
```

### `HTTP 451` from Binance

Geo-block. Use VPN, or edit fetch scripts:

```python
BASE_URL = "https://data-api.binance.vision"
```

### Port already in use

```powershell
netstat -ano | findstr :8000
taskkill /F /PID <pid>
```

### Web UI shows "API offline"

Server isn't running:

```powershell
python scripts_python\web\api.py
```

Verify:

```powershell
curl http://localhost:8000/api/health
```

### Empty features table

```powershell
python -m scripts_python.fetch_futures
python -m scripts_python.fetch_funding
python -m scripts_python.build_features
```

### Empty setups

```powershell
python -m scripts_python.opportunity
```

"No setups today" = correct when market doesn't match any strategy.

### `Could not resolve host: github.com`

Network blocks GitHub. Use mobile hotspot, or:

```powershell
git remote set-url origin https://gh-proxy.com/https://github.com/sachinchakrawarti69/eth_bot.git
git pull
git remote set-url origin https://github.com/sachinchakrawarti69/eth_bot.git
```

### `PermissionError: file in use`

Excel has the file open. Kill it:

```powershell
Stop-Process -Name EXCEL -Force -ErrorAction SilentlyContinue
```

---

## 19. Cheat sheet

```powershell
# daily refresh
python -m scripts_python.fetch_futures; python -m scripts_python.fetch_funding; python -m scripts_python.build_features; python -m scripts_python.compute_sr

# scan for setups
python -m scripts_python.opportunity

# view in browser
python scripts_python\web\api.py     # then http://localhost:8000

# auto-commit while working
python git_auto_push.py --no-push
```

Three commands + one watcher.

---

## 20. Ports

| Service | Port | URL |
|---|---|---|
| Flask API + UI | 8000 | http://localhost:8000 |
| Jupyter Lab | 8888 | opens automatically |
| Streamlit (optional) | 8501 | http://localhost:8501 |

---

## 21. Files

| What | Where |
|---|---|
| Live DB | `database/market.db` |
| Options DB | `database/options.db` |
| Schemas | `database/schema/*.sql`, `database/schema/options/*.sql` |
| Fetchers | `scripts_python/fetch_*.py` |
| Features | `scripts_python/build_features.py` |
| S/R | `scripts_python/compute_sr.py` |
| Stats | `scripts_python/statistical_mode.py` |
| Backtest | `scripts_python/backtest.py` |
| Opportunity | `scripts_python/opportunity.py` |
| Web UI | `web/trade_desk.html` |
| Web API | `scripts_python/web/api.py` |
| Reports | `reports/daily/`, `reports/orders/` |
| Exports | `exports/*.xlsx` |
| Notebooks | `analysis/*/` |
| Commit messages | `commit_messages.py` |
| Auto-push | `git_auto_push.py` |