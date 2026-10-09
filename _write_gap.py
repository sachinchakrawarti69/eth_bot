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
            out = "  " + c(f, C.CYN) + "  " + c(self.msg, C.GRY)
            sys.stdout.write(out)
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)


def do_once(do_push, dry_run, spin, state):
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

    line1 = ("  " + c(ts, C.GRY) + "  " +
             c("changes", C.WHT, True) + "  " +
             c(str(n), C.YEL, True) + "  " +
             c(subject, C.MAG, True))
    print(line1)

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
    else:
        last = err.splitlines()[-1] if err else "unknown"
        print("           " + c("✗ push failed", C.RED, True) + "  " + c(last[:50], C.GRY))


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


def watch(interval, do_push, dry_run):
    ansi_on()
    bn = branch()
    state = {"commits": 0, "pushes": 0}
    spin = Spinner()

    print()
    title = c("git auto push", C.B + C.WHT)
    print("  " + title + "  " + c("repo", C.GRY) + " " + str(REPO_ROOT))
    line = (
        "  " + c("branch", C.GRY) + " " + c(bn, C.YEL, True) + "   " +
        c("interval", C.GRY) + " " + str(interval) + "s   " +
        c("push", C.GRY) + " " + ("on" if do_push else "off") + "   " +
        c("messages", C.GRY) + " " +
        ("commit_messages.py" if HAVE_CM else "fallback")
    )
    print(line)
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
                do_once(do_push, dry_run, spin, state)
                idle_since = time.time()
                time.sleep(1)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                clear_line()
                print("  " + c("error", C.RED, True) + " " + type(e).__name__ + ": " + str(e))
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