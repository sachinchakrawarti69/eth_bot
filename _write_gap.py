from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "git_auto_push.py"

CODE = r'''"""Git auto-commit + push. Compact single-line UI.

Run:
    python git_auto_push.py                 # watch
    python git_auto_push.py --no-push       # commit only
    python git_auto_push.py --once          # single pass
    python git_auto_push.py --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    from commit_messages import build_message, git_status as cm_git_status
    HAVE_CM = True
except ImportError:
    HAVE_CM = False


REPO_ROOT        = Path(__file__).resolve().parent
DEFAULT_INTERVAL = 30


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
    return f"{C.B if b else ''}{col}{t}{C.R}"


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
            i += 1; continue
        code, path = e[:2], e[3:]
        if code[0] == "R":
            np = parts[i+1] if i+1 < len(parts) else ""
            res.append(("R", f"{path} -> {np}")); i += 2
        else:
            res.append((code.strip() or "??", path)); i += 1
    return res


def commit(msg):
    r = subprocess.run(["git", "commit", "-F", "-"], cwd=str(REPO_ROOT),
                       input=msg, text=True, encoding="utf-8",
                       capture_output=True)
    if r.returncode != 0:
        if "nothing to commit" in (r.stderr or r.stdout).lower():
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
        if self.t: self.t.join(timeout=0.5)
        clear_line()

    def _run(self):
        i = 0
        while not self.stop:
            f = FRAMES[i % len(FRAMES)]
            clear_line()
            sys.stdout.write(f"  {c(f, C.CYN)}  {c(self.msg, C.GRY)}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)


# ================================================================
#  MAIN LOOP
# ================================================================

def do_once(do_push, dry_run, spin, state):
    changes = status()
    if not changes:
        return

    # message
    if HAVE_CM:
        msg = build_message(changes)
    else:
        msg = f"update {len(changes)} files"
    subject = msg.splitlines()[0]

    # show what changed
    clear_line()
    ts = datetime.now().strftime("%H:%M:%S")
    n = len(changes)
    print(f"  {c(ts, C.GRY)}  "
          f"{c('changes', C.WHT, True)}  {c(str(n), C.YEL, True)}  "
          f"{c(subject, C.MAG, True)}")

    # list files (max 5)
    for st, p in changes[:5]:
        col = {"M": C.YEL, "A": C.GRN, "D": C.RED, "R": C.CYN, "??": C.GRN}.get(st, C.WHT)
        short = p.replace("eth_bot_v2/", "")
        print(f"           {c(st.ljust(2), col, True)} {c(short, C.GRY)}")
    if n > 5:
        print(f"           {c(f'... +{n-5} more', C.GRY)}")

    if dry_run:
        print(f"           {c('dry-run — skipped', C.YEL)}")
        return

    # stage
    spin.start("staging")
    git("add", "-A")
    spin.end()

    staged, _ = git("diff", "--cached", "--name-only")
    if not staged:
        print(f"           {c('nothing staged', C.GRY)}")
        return

    # commit
    spin.start("committing")
    try:
        ok = commit(msg)
    finally:
        spin.end()

    if not ok:
        print(f"           {c('nothing to commit', C.GRY)}")
        return

    state["commits"] += 1
    print(f"           {c('✓ committed', C.GRN, True)}")

    if not do_push:
        return
    if not has_remote():
        print(f"           {c('! no remote', C.YEL)}")
        return

    spin.start("pushing")
    try:
        ok, err = push()
    finally:
        spin.end()

    if ok:
        state["pushes"] += 1
        print(f"           {c('↑ pushed', C.CYN, True)}")
    else:
        last = err.splitlines()[-1] if err else "unknown"
        print(f"           {c('✗ push failed', C.RED, True)}  {c(last[:50], C.GRY)}")


def render_idle(branch_name, interval, remaining, state, spin_i, idle_since):
    """One line redraw."""
    spin = FRAMES[spin_i % len(FRAMES)]
    idle = int(time.time() - idle_since)
    im, isec = divmod(idle, 60)
    idle_str = f"{im:02d}:{isec:02d}"

    # progress bar
    w = 20
    filled = int(w * (1 - remaining / interval)) if interval else 0
    bar = "█" * filled + "░" * (w - filled)

    line = (f"  {c(spin, C.CYN)} "
            f"{c(branch_name, C.YEL, True)}  "
            f"{c(bar, C.BLU)}  "
            f"{c(f'{int(remaining)}s', C.WHT)}  "
            f"{c('idle', C.GRY)} {c(idle_str, C.GRY)}  "
            f"{c(f'c{state[\"commits\"]}', C.MAG)} "
            f"{c(f'p{state[\"pushes\"]}', C.CYN)}  "
            f"{c('Ctrl+C to stop', C.GRY)}")
    clear_line()
    sys.stdout.write(line)
    sys.stdout.flush()


def watch(interval, do_push, dry_run):
    ansi_on()
    bn = branch()
    state = {"commits": 0, "pushes": 0}
    spin = Spinner()

    print()
    print(f"  {c('git auto push', C.B + C.WHT)}  "
          f"{c('repo', C.GRY)} {REPO_ROOT}")
    print(f"  {c('branch', C.GRY)} {c(bn, C.YEL, True)}   "
          f"{c('interval', C.GRY)} {interval}s   "
          f"{c('push', C.GRY)} {'on' if do_push else 'off'}   "
          f"{c('messages', C.GRY)} "
          f"{'commit_messages.py' if HAVE_CM else 'fallback'}")
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

                    # peek for changes every 2s
                    if time.time() - last_peek >= 2:
                        last_peek = time.time()
                        if status():
                            break

                # do work
                clear_line()
                do_once(do_push, dry_run, spin, state)
                idle_since = time.time()

                # brief pause
                time.sleep(1)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                clear_line()
                print(f"  {c('error', C.RED, True)} {type(e).__name__}: {e}")
                time.sleep(interval)

    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        clear_line()
        print()
        print(f"  {c('stopped', C.YEL, True)}   "
              f"{c('runtime', C.GRY)} {int(time.time() - idle_since)}s   "
              f"{c('commits', C.GRY)} {c(state['commits'], C.MAG, True)}   "
              f"{c('pushes', C.GRY)} {c(state['pushes'], C.CYN, True)}")
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
    args = ap.parse_args()

    ansi_on()

    if args.once or args.dry_run:
        spin = Spinner()
        state = {"commits": 0, "pushes": 0}
        do_once(not args.no_push, args.dry_run, spin, state)
        return 0

    watch(args.interval, not args.no_push, False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

TARGET.write_text(CODE, encoding="utf-8")
print("wrote", TARGET)
print("size:", TARGET.stat().st_size, "bytes")
print("lines:", CODE.count("\n") + 1)

import ast
ast.parse(CODE)
print("syntax OK")