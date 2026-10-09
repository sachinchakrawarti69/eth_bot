cd "D:\Sachin Chakrawarti\Learn\done\eth_bot"
python git_auto_push.py --dry-run

Single pass:

powershell
python git_auto_push.py --once


Watch mode (runs forever):

powershell
python git_auto_push.py


Watch mode without push (commit only):

powershell
python git_auto_push.py --no-push


Custom interval (every 15 seconds):

powershell
python git_auto_push.py --interval 15