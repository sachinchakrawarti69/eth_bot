"""Git auto-commit + push with notifications.

Notifies on commit and push:
  - Windows toast (native)
  - Windows beep (fallback)
  - Optional Discord / Slack webhook

Run:
    python git_auto_push.py                 # watch
    python git_auto_push.py --no-push       # commit only
    python git_auto_push.py --once          # single pass
    python git_auto_push.py --dry-run
    python git_auto_push.py --no-notify     # disable toasts
    python git_auto_push.py --notify-push   # only notify on push
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from commit_messages import build_message, git_status as cm_git_status
    HAVE_CM = True
except ImportError:
    HAVE_CM = False


REPO_ROOT        = Path(__file__).resolve().parent
DEFAULT_INTERVAL = 30
CONFIG_FILE      = REPO_ROOT / ".git_auto_push.json"


# ================================================================
#  CONFIG
# ================================================================

DEFAULT_CONFIG = {
    "notify":           True,       # toast on commit
    "notify_push":      False,      # if True, only notify on push (not commit)
    "beep":             True,       # play a beep
    "discord_webhook":  "",         # paste URL to enable Discord alerts
    "slack_webhook":    "",         # paste URL to enable Slack alerts
    "toast_duration":   "short",    # "short" or "long"
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def save_default_config():
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        print(f"  wrote default config: {CONFIG_FILE.name}")


# ================================================================
#  COLORS
# ================================================================

class C:
    R = "\033[0m"
    B = "\033[1m"
    D = "\033[2m"
    RED = "\033[31m"
    GRN = "\033[32m"
    YEL = "\033[33m"
    BLU = "\033[34m"
    MAG = "\033[35m"
    CYN = "\033[36m"
    WHT = "\033[37m"
    GRY = "\033[90m"


def ansi_on():
    if sys.platform == "win32":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass


def c(t, col, b=False):
    bold = C.B if b else ""
    return bold + col + t + C.R


def clear_line():
    sys.stdout.write("\033[2K\r")
    sys.stdout.flush()


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


# ================================================================
#  NOTIFICATIONS
# ================================================================

class Notifier:
    """Sends Windows toasts, beeps, and webhooks."""

    def __init__(self, config: dict):
        self.cfg = config
        self.have_plyer = False
        self.have_win10toast = False
        self.have_powershell = sys.platform == "win32"
        self._probe()

    def _probe(self):
        try:
            from plyer import notification  # noqa
            self.have_plyer = True
        except Exception:
            pass
        try:
            from win10toast import ToastNotifier  # noqa
            self.have_win10toast = True
        except Exception:
            pass

    # ---------- Windows toast ----------

    def toast(self, title: str, msg: str, duration: str = "short"):
        """Try plyer → win10toast → PowerShell → beep."""
        if self.have_plyer:
            try:
                from plyer import notification
                notification.notify(
                    title=title, message=msg,
                    timeout=5 if duration == "short" else 10,
                    app_name="Git Auto Push")
                return True
            except Exception:
                pass

        if self.have_win10toast:
            try:
                from win10toast import ToastNotifier
                n = ToastNotifier()
                n.show_toast(title, msg, duration=5, threaded=True)
                return True
            except Exception:
                pass

        if self.have_powershell:
            try:
                # escape for PowerShell single-quoted string
                t = title.replace("'", "''")
                m = msg.replace("'", "''")
                ps = (
                    "[reflection.assembly]::loadwithpartialname("
                    "'System.Windows.Forms') | Out-Null; "
                    "[reflection.assembly]::loadwithpartialname("
                    "'System.Drawing') | Out-Null; "
                    "$notify = New-Object System.Windows.Forms.NotifyIcon; "
                    "$notify.Icon = [System.Drawing.SystemIcons]::Information; "
                    "$notify.Visible = $true; "
                    f"$notify.ShowBalloonTip(5000, '{t}', '{m}', "
                    "[System.Windows.Forms.ToolTipIcon]::Info); "
                    "Start-Sleep -Milliseconds 300; "
                    "$notify.Dispose()"
                )
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden",
                     "-Command", ps],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                return True
            except Exception:
                pass
        return False

    def beep(self):
        if not self.cfg.get("beep"):
            return
        try:
            if sys.platform == "win32":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                sys.stdout.write("\a")
                sys.stdout.flush()
        except Exception:
            pass

    # ---------- webhooks ----------

    def discord(self, msg: str):
        url = self.cfg.get("discord_webhook") or ""
        if not url:
            return False
        try:
            data = json.dumps({"content": msg}).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST")
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception:
            return False

    def slack(self, msg: str):
        url = self.cfg.get("slack_webhook") or ""
        if not url:
            return False
        try:
            data = json.dumps({"text": msg}).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST")
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception:
            return False

    # ---------- high-level ----------

    def notify_commit(self, subject: str, files: int):
        if not self.cfg.get("notify"):
            return
        if self.cfg.get("notify_push"):
            return   # only notify on push
        title = "Git commit"
        msg = subject
        self.toast(title, msg, self.cfg.get("toast_duration", "short"))
        self.beep()
        self.discord(f"**{title}**\n`{subject}`\n_{files} file(s)_")
        self.slack(f"*{title}*\n`{subject}`\n_{files} file(s)_")

    def notify_push(self, subject: str):
        if not self.cfg.get("notify"):
            return
        title = "Git push"
        msg = subject
        self.toast(title, msg, self.cfg.get("toast_duration", "short"))
        self.beep()
        self.discord(f"**{title}**\n`{subject}`")
        self.slack(f"*{title}*\n`{subject}`")

    def notify_error(self, subject: str):
        if not self.cfg.get("notify"):
            return
        title = "Git error"
        msg = subject
        self.toast(title, msg, "long")
        # double beep on error
        self.beep()
        time.sleep(0.15)
        self.beep()
        self.discord(f"**{title}**\n`{subject}`")
        self.slack(f"*{title}*\n`{subject}`")


# ================================================================
#  GIT
# ================================================================

def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=str(REPO_ROOT),
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return (r.stdout or "").strip(), r.returncode


def branch():
    out, _ = git("rev-parse", "--abbrev-ref", "HEAD")
    return out or "main"


def has_remote():
    out, rc = git("remote", "get-url", "origin")
    return rc == 0 and bool(out)


def status():
    if HAVE_CM:
        return cm_git_status()
    out, _ = git("status", "--porcelain=v1", "-z")
    if not out:
        return []
    parts = out.split("\x00")
    res, i = [], 0
    while i < len(parts):
        e = parts[i]
        if not e:
            i += 1
            continue
        code = e[:2]
        path = e[3:]
        if code[0] == "R":
            np = parts[i+1] if i+1 < len(parts) else ""
            res.append(("R", path + " -> " + np))
            i += 2
        else:
            res.append((code.strip() or "??", path))
            i += 1
    return res


def commit(msg):
    r = subprocess.run(["git", "commit", "-F", "-"], cwd=str(REPO_ROOT),
                       input=msg, text=True, encoding="utf-8",
                       capture_output=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout).lower()
        if "nothing to commit" in err:
            return False
        raise RuntimeError((r.stderr or r.stdout).strip())
    return True


def push():
    r = subprocess.run(["git", "push", "origin", branch()],
                       cwd=str(REPO_ROOT), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return r.returncode == 0, (r.stderr or r.stdout).strip()


# ================================================================
#  SPINNER
# ================================================================

FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class Spinner:
    def __init__(self):
        self.stop = False
        self.msg = ""
        self.t = None

    def start(self, msg):
        self.msg = msg
        self.stop = False
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()

    def set(self, msg):
        self.msg = msg

    def end(self):
        self.stop = True
        if self.t:
            self.t.join(timeout=0.5)
        clear_line()

    def _run(self):
        i = 0
        while not self.stop:
            f = FRAMES[i % len(FRAMES)]
            clear_line()
            sys.stdout.write("  " + c(f, C.CYN) + "  " + c(self.msg, C.GRY))
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)


# ================================================================
#  MAIN LOGIC
# ================================================================

def do_once(do_push, dry_run, spin, state, notifier: Notifier):
    changes = status()
    if not changes:
        return

    if HAVE_CM:
        msg = build_message(changes)
    else:
        msg = "update " + str(len(changes)) + " files"
    subject = msg.splitlines()[0]

    clear_line()
    ts = datetime.now().strftime("%H:%M:%S")
    n = len(changes)

    print("  " + c(ts, C.GRY) + "  " +
          c("changes", C.WHT, True) + "  " +
          c(str(n), C.YEL, True) + "  " +
          c(subject, C.MAG, True))

    for st, p in changes[:5]:
        col = {"M": C.YEL, "A": C.GRN, "D": C.RED, "R": C.CYN, "??": C.GRN}.get(st, C.WHT)
        short = p.replace("eth_bot_v2/", "")
        print("           " + c(st.ljust(2), col, True) + " " + c(short, C.GRY))
    if n > 5:
        print("           " + c("... +" + str(n-5) + " more", C.GRY))

    if dry_run:
        print("           " + c("dry-run — skipped", C.YEL))
        return

    spin.start("staging")
    git("add", "-A")
    spin.end()

    staged, _ = git("diff", "--cached", "--name-only")
    if not staged:
        print("           " + c("nothing staged", C.GRY))
        return

    spin.start("committing")
    try:
        ok = commit(msg)
    finally:
        spin.end()

    if not ok:
        print("           " + c("nothing to commit", C.GRY))
        return

    state["commits"] += 1
    print("           " + c("✓ committed", C.GRN, True))
    notifier.notify_commit(subject, n)

    if not do_push:
        return
    if not has_remote():
        print("           " + c("! no remote", C.YEL))
        return

    spin.start("pushing")
    try:
        ok, err = push()
    finally:
        spin.end()

    if ok:
        state["pushes"] += 1
        print("           " + c("↑ pushed", C.CYN, True))
        notifier.notify_push(subject)
    else:
        last = err.splitlines()[-1] if err else "unknown"
        print("           " + c("✗ push failed", C.RED, True) + "  " + c(last[:50], C.GRY))
        notifier.notify_error("push failed: " + last[:80])


def render_idle(branch_name, interval, remaining, state, spin_i, idle_since):
    spin = FRAMES[spin_i % len(FRAMES)]
    idle = int(time.time() - idle_since)
    im, isec = divmod(idle, 60)
    idle_str = str(im).zfill(2) + ":" + str(isec).zfill(2)

    w = 20
    filled = int(w * (1 - remaining / interval)) if interval else 0
    bar = "█" * filled + "░" * (w - filled)

    commits = state["commits"]
    pushes = state["pushes"]
    rem_s = str(int(remaining)) + "s"

    line = (
        "  " + c(spin, C.CYN) + " " +
        c(branch_name, C.YEL, True) + "  " +
        c(bar, C.BLU) + "  " +
        c(rem_s, C.WHT) + "  " +
        c("idle", C.GRY) + " " + c(idle_str, C.GRY) + "  " +
        c("c" + str(commits), C.MAG) + " " +
        c("p" + str(pushes), C.CYN) + "  " +
        c("Ctrl+C to stop", C.GRY)
    )
    clear_line()
    sys.stdout.write(line)
    sys.stdout.flush()


def watch(interval, do_push, dry_run, notifier: Notifier):
    ansi_on()
    bn = branch()
    state = {"commits": 0, "pushes": 0}
    spin = Spinner()

    print()
    print("  " + c("git auto push", C.B + C.WHT) + "  " +
          c("repo", C.GRY) + " " + str(REPO_ROOT))
    print("  " + c("branch", C.GRY) + " " + c(bn, C.YEL, True) + "   " +
          c("interval", C.GRY) + " " + str(interval) + "s   " +
          c("push", C.GRY) + " " + ("on" if do_push else "off") + "   " +
          c("messages", C.GRY) + " " +
          ("commit_messages.py" if HAVE_CM else "fallback") + "   " +
          c("notify", C.GRY) + " " +
          ("on" if notifier.cfg.get("notify") else "off"))
    print()

    hide_cursor()
    idle_since = time.time()
    spin_i = 0
    try:
        while True:
            try:
                end = time.time() + interval
                last_peek = 0
                while time.time() < end:
                    rem = end - time.time()
                    render_idle(bn, interval, rem, state, spin_i, idle_since)
                    spin_i += 1
                    time.sleep(0.1)

                    if time.time() - last_peek >= 2:
                        last_peek = time.time()
                        if status():
                            break

                clear_line()
                do_once(do_push, dry_run, spin, state, notifier)
                idle_since = time.time()
                time.sleep(1)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                clear_line()
                print("  " + c("error", C.RED, True) + " " +
                      type(e).__name__ + ": " + str(e))
                notifier.notify_error(type(e).__name__ + ": " + str(e)[:80])
                time.sleep(interval)

    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        clear_line()
        print()
        commits = state["commits"]
        pushes = state["pushes"]
        print("  " + c("stopped", C.YEL, True) + "   " +
              c("commits", C.GRY) + " " + c(str(commits), C.MAG, True) + "   " +
              c("pushes", C.GRY) + " " + c(str(pushes), C.CYN, True))
        print()


# ================================================================
#  CLI
# ================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    ap.add_argument("--no-notify", action="store_true",
                    help="disable all notifications")
    ap.add_argument("--notify-push", action="store_true",
                    help="notify only on push, not on commit")
    ap.add_argument("--init-config", action="store_true",
                    help="write a default .git_auto_push.json")
    args = ap.parse_args()

    ansi_on()

    if args.init_config:
        save_default_config()
        return 0

    cfg = load_config()
    if args.no_notify:
        cfg["notify"] = False
    if args.notify_push:
        cfg["notify_push"] = True

    notifier = Notifier(cfg)

    if args.once or args.dry_run:
        spin = Spinner()
        state = {"commits": 0, "pushes": 0}
        do_once(not args.no_push, args.dry_run, spin, state, notifier)
        return 0

    watch(args.interval, not args.no_push, False, notifier)
    return 0


if __name__ == "__main__":
    sys.exit(main())
