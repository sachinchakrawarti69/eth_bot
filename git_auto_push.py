"""Git auto-commit and push with animated TUI.

Uses `commit_messages.py` for message generation.

Run:
    python git_auto_push.py                    # watch mode
    python git_auto_push.py --once
    python git_auto_push.py --no-push
    python git_auto_push.py --dry-run
    python git_auto_push.py --interval 15
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

try:
    from commit_messages import build_message, git_status as cm_git_status
    HAVE_CM = True
except ImportError:
    HAVE_CM = False


REPO_ROOT        = Path(__file__).resolve().parent
DEFAULT_INTERVAL = 30
LOG_LINES        = 10
WAITING_FPS      = 12       # frames per second for the waiting animation


# ================================================================
#  COLORS
# ================================================================

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[31m"
    GREEN  = "\033[32m"
    YELLOW = "\033[33m"
    BLUE   = "\033[34m"
    MAGENTA= "\033[35m"
    CYAN   = "\033[36m"
    WHITE  = "\033[37m"
    GREY   = "\033[90m"


def enable_ansi():
    if sys.platform == "win32":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass


def clear_screen():
    if sys.platform == "win32":
        sys.stdout.write("\033[2J\033[H")
    else:
        sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def clear_line():
    sys.stdout.write("\033[2K\r")


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def c(text, color, bold=False):
    b = C.BOLD if bold else ""
    return f"{b}{color}{text}{C.RESET}"


def box_top(title="", n=66):
    if title:
        pad = n - len(title) - 4
        if pad < 0: pad = 0
        return c("┌─ ", C.CYAN) + c(title, C.CYAN, bold=True) + c(" " + "─" * pad + "┐", C.CYAN)
    return c("┌" + "─" * (n - 2) + "┐", C.CYAN)


def box_bottom(n=66):
    return c("└" + "─" * (n - 2) + "┘", C.CYAN)


def box_line(text="", n=66):
    import re
    visible = re.sub(r"\033\[[0-9;]*m", "", text)
    pad = n - 2 - len(visible)
    if pad < 0: pad = 0
    return c("│", C.CYAN) + " " + text + " " * pad + c("│", C.CYAN)


# ================================================================
#  WAITING ANIMATIONS
# ================================================================

class WaitingAnimator:
    """Rotating animation states for the idle mode."""

    # breathing pulse bar
    PULSE_BAR_W = 40

    # rotating messages
    QUOTES = [
        "watching for file changes",
        "listening to disk events",
        "awaiting next save",
        "monitoring workspace",
        "tracking repo state",
        "any change will be committed",
        "idle — waiting",
    ]

    # spinner frames for the idle dot
    SPIN = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    # ripples
    RIPPLES = ["·", "˙", "•", "●", "•", "˙"]

    def __init__(self):
        self.t0 = time.time()
        self.idx = 0
        self.quote_idx = 0
        self.quote_switch_every = 3.0    # seconds
        self._last_quote_switch = time.time()

    def pulse_bar(self) -> str:
        """A bar that breathes in and out."""
        w = self.PULSE_BAR_W
        t = time.time() * 1.4
        import math
        # sine wave gives smooth in/out
        phase = (math.sin(t) + 1) / 2     # 0..1
        filled = int(w * phase)
        # color ramps from dim-blue to bright-cyan based on phase
        if phase < 0.33:
            col = C.GREY
        elif phase < 0.66:
            col = C.BLUE
        else:
            col = C.CYAN
        return c("█" * filled, col) + c("░" * (w - filled), C.GREY)

    def spinner(self) -> str:
        f = self.SPIN[int((time.time() * WAITING_FPS) % len(self.SPIN))]
        return c(f, C.CYAN)

    def ripple(self) -> str:
        """A single dot that pulses through shapes."""
        i = int((time.time() * 6) % len(self.RIPPLES))
        return c(self.RIPPLES[i], C.CYAN)

    def elapsed_str(self) -> str:
        s = int(time.time() - self.t0)
        m, ss = divmod(s, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{ss:02d}"
        return f"{m:02d}:{ss:02d}"

    def current_quote(self) -> str:
        now = time.time()
        if now - self._last_quote_switch >= self.quote_switch_every:
            self._last_quote_switch = now
            self.quote_idx = (self.quote_idx + 1) % len(self.QUOTES)
        return self.QUOTES[self.quote_idx]


# ================================================================
#  WORKING SPINNER (for actual git ops)
# ================================================================

class Spinner:
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self):
        self._stop = threading.Event()
        self._msg = ""
        self._frame = 0
        self._thread = None

    def start(self, msg="working"):
        self._msg = msg
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update(self, msg):
        self._msg = msg

    def stop(self, clear=True):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        if clear:
            clear_line()

    def _run(self):
        while not self._stop.is_set():
            f = self.FRAMES[self._frame % len(self.FRAMES)]
            clear_line()
            sys.stdout.write(f"  {c(f, C.YELLOW)}  {c(self._msg, C.DIM)}")
            sys.stdout.flush()
            self._frame += 1
            time.sleep(0.08)


# ================================================================
#  EVENT LOG
# ================================================================

class EventLog:
    def __init__(self, maxlen=LOG_LINES):
        self.events = deque(maxlen=maxlen)

    def add(self, kind, msg, detail=""):
        ts = datetime.now().strftime("%H:%M:%S")
        self.events.append((ts, kind, msg, detail))

    def render(self):
        if not self.events:
            return c("  (no events yet)", C.DIM)
        lines = []
        for ts, kind, msg, detail in self.events:
            icon = {
                "info":   c("•", C.BLUE),
                "ok":     c("✓", C.GREEN, bold=True),
                "warn":   c("!", C.YELLOW),
                "error":  c("✗", C.RED, bold=True),
                "commit": c("◆", C.MAGENTA, bold=True),
                "push":   c("↑", C.CYAN, bold=True),
                "start":  c("▶", C.GREEN, bold=True),
            }.get(kind, " ")
            tss = c(ts, C.GREY)
            m = msg
            if detail:
                m += " " + c(detail, C.GREY)
            lines.append(f"  {tss}  {icon}  {m}")
        return "\n".join(lines)


# ================================================================
#  GIT WRAPPER
# ================================================================

def git(*args, check=True, capture=True):
    cmd = ["git"] + list(args)
    r = subprocess.run(
        cmd, cwd=str(REPO_ROOT),
        capture_output=capture, text=True,
        encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {err}")
    return (r.stdout or "").strip()


def is_repo():
    try:
        git("rev-parse", "--is-inside-work-tree")
        return True
    except Exception:
        return False


def has_remote():
    try:
        return bool(git("remote", "get-url", "origin"))
    except Exception:
        return False


def current_branch():
    try:
        return git("rev-parse", "--abbrev-ref", "HEAD")
    except Exception:
        return "main"


def get_status():
    if HAVE_CM:
        return cm_git_status()
    out = git("status", "--porcelain=v1", "-z")
    if not out:
        return []
    parts = out.split("\x00")
    result = []
    i = 0
    while i < len(parts):
        entry = parts[i]
        if not entry:
            i += 1
            continue
        code = entry[:2]
        path = entry[3:]
        if code[0] == "R":
            new_path = parts[i+1] if i+1 < len(parts) else ""
            result.append(("R", f"{path} -> {new_path}"))
            i += 2
        else:
            result.append((code.strip() or "??", path))
            i += 1
    return result


# ================================================================
#  COMMIT + PUSH
# ================================================================

def stage_all():
    git("add", "-A")


def has_staged():
    return bool(git("diff", "--cached", "--name-only").strip())


def do_commit(msg):
    r = subprocess.run(
        ["git", "commit", "-F", "-"],
        cwd=str(REPO_ROOT),
        input=msg, text=True, encoding="utf-8",
        capture_output=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        if "nothing to commit" in err.lower():
            return False
        raise RuntimeError(err)
    return True


def do_push():
    branch = current_branch()
    r = subprocess.run(
        ["git", "push", "origin", branch],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    return r.returncode == 0, ((r.stdout or "") + "\n" + (r.stderr or "")).strip()


# ================================================================
#  HEADER
# ================================================================

def render_header(branch, interval, do_push, dry_run, commits, pushes, uptime):
    m, s = divmod(int(uptime), 60)
    h, m = divmod(m, 60)
    up = f"{h:02d}:{m:02d}:{s:02d}"

    print()
    print(box_top("◆ GIT AUTO PUSH", 66))
    print(box_line(f"  {c('repo',     C.GREY)}   {REPO_ROOT}"))
    print(box_line(f"  {c('branch',   C.GREY)}   {c(branch, C.YELLOW, bold=True)}"))
    print(box_line(f"  {c('interval', C.GREY)}   every {c(str(interval)+'s', C.WHITE, bold=True)}"))
    print(box_line(f"  {c('push',     C.GREY)}   "
                   + (c("enabled", C.GREEN, bold=True) if do_push else c("disabled", C.GREY))
                   + (c("   [DRY RUN]", C.YELLOW, bold=True) if dry_run else "")))
    print(box_line(f"  {c('messages', C.GREY)}   "
                   + (c("external commit_messages.py", C.GREEN) if HAVE_CM
                      else c("built-in fallback", C.YELLOW))))
    print(box_line(f"  {c('uptime',   C.GREY)}   {c(up, C.WHITE)}    "
                   f"{c('commits', C.GREY)} {c(str(commits), C.MAGENTA, bold=True)}    "
                   f"{c('pushes', C.GREY)} {c(str(pushes), C.CYAN, bold=True)}"))
    print(box_bottom(66))
    print()


# ================================================================
#  WAITING PANEL
# ================================================================

def render_waiting_panel(anim: WaitingAnimator, next_tick: float,
                         interval: int, log: EventLog, changes_count: int):
    """The panel shown when no changes exist."""
    print(box_top("◌ WAITING FOR CHANGES", 66))

    # Row 1: spinner + quote
    spinner = anim.spinner()
    quote = anim.current_quote()
    print(box_line(f"    {spinner}  {c(quote, C.WHITE, bold=True)}"))

    # Row 2: pulse bar
    print(box_line(f"    {anim.pulse_bar()}"))

    # Row 3: timer
    elapsed = anim.elapsed_str()
    remain = max(0, next_tick - time.time())
    print(box_line(f"    {c('idle for', C.GREY)} {c(elapsed, C.CYAN, bold=True)}"
                   f"   {c('next check in', C.GREY)} {c(f'{int(remain)}s', C.YELLOW, bold=True)}"))

    # Row 4: countdown progress bar
    bar_w = 40
    filled = int(bar_w * (1 - remain / interval)) if interval else 0
    bar = c("█" * filled, C.BLUE) + c("░" * (bar_w - filled), C.GREY)
    print(box_line(f"    {bar}"))

    print(box_bottom(66))


# ================================================================
#  DRAW
# ================================================================

def draw_waiting(anim, log, next_tick, commits, pushes, branch, interval,
                 do_push, dry_run, uptime):
    clear_screen()
    render_header(branch, interval, do_push, dry_run, commits, pushes, uptime)
    render_waiting_panel(anim, next_tick, interval, log, 0)

    print()
    print(box_top("● RECENT EVENTS", 66))
    for line in log.render().split("\n"):
        print(box_line(line))
    print(box_bottom(66))
    print()

    print(f"  {c('Ctrl+C to stop', C.GREY)}")
    print()


def draw_working(log, commits, pushes, branch, interval, do_push, dry_run, uptime):
    clear_screen()
    render_header(branch, interval, do_push, dry_run, commits, pushes, uptime)
    print(box_top("● RECENT EVENTS", 66))
    for line in log.render().split("\n"):
        print(box_line(line))
    print(box_bottom(66))
    print()


# ================================================================
#  PROCESS
# ================================================================

def process_once(do_push, dry_run, log, spinner, anim, branch, interval,
                 commits, pushes, t0):
    spinner.start("checking for changes")
    changes = get_status()
    spinner.stop()

    if not changes:
        return False, False

    log.add("info", f"{len(changes)} change{'s' if len(changes) != 1 else ''} detected")

    draw_working(log, commits, pushes, branch, interval, do_push, dry_run,
                 time.time() - t0)

    print(f"  {c('changes:', C.WHITE, bold=True)}")
    for status, path in changes[:20]:
        color = {
            "M":  C.YELLOW,
            "A":  C.GREEN,
            "D":  C.RED,
            "R":  C.CYAN,
            "??": C.GREEN,
        }.get(status, C.WHITE)
        short = path
        if short.startswith("eth_bot_v2/"):
            short = short[len("eth_bot_v2/"):]
        print(f"    {c(status.ljust(3), color, bold=True)} {short}")
    if len(changes) > 20:
        print(f"    {c(f'... and {len(changes)-20} more', C.GREY)}")

    if HAVE_CM:
        msg = build_message(changes)
    else:
        msg = _fallback_message(changes)

    subject = msg.splitlines()[0]
    print()
    print(f"  {c('commit message:', C.WHITE, bold=True)}")
    print(f"    {c(subject, C.MAGENTA, bold=True)}")

    if dry_run:
        log.add("warn", "dry run — no commit", f"({len(changes)} files)")
        return False, False

    spinner.start("staging files")
    stage_all()
    spinner.stop()

    if not has_staged():
        log.add("warn", "nothing staged")
        return False, False

    spinner.start("committing")
    ok = do_commit(msg)
    spinner.stop()

    if not ok:
        log.add("warn", "nothing to commit")
        return False, False

    log.add("commit", f"committed {c(subject[:40], C.MAGENTA)}")
    print(f"  {c('✓ committed', C.GREEN, bold=True)}")

    if not do_push:
        log.add("info", "push skipped (--no-push)")
        return True, False

    if not has_remote():
        log.add("warn", "no remote 'origin'")
        return True, False

    spinner.start("pushing to origin")
    ok, out = do_push()
    spinner.stop()

    if ok:
        log.add("push", "pushed to origin")
        print(f"  {c('↑ pushed', C.CYAN, bold=True)}")
        return True, True
    else:
        err_lines = [l for l in out.splitlines() if l.strip()]
        short = err_lines[-1] if err_lines else "unknown"
        log.add("error", "push failed", f"{c(short[:50], C.RED)}")
        print(f"  {c('✗ push failed', C.RED, bold=True)}: {short}")
        return True, False


def _fallback_message(changes):
    n = len(changes)
    if n == 1:
        status, path = changes[0]
        return f"{status} {Path(path).name}"
    return f"update {n} files"


# ================================================================
#  WATCH
# ================================================================

def watch(interval, do_push, dry_run):
    enable_ansi()

    log = EventLog(maxlen=LOG_LINES)
    spinner = Spinner()
    anim = WaitingAnimator()

    branch = current_branch()
    t0 = time.time()
    commits = 0
    pushes = 0

    log.add("start", "watching", f"{REPO_ROOT}")
    if HAVE_CM:
        log.add("ok", "using commit_messages.py")
    else:
        log.add("warn", "commit_messages.py not found — fallback")
    if not has_remote():
        log.add("warn", "no remote 'origin' configured")

    hide_cursor()
    try:
        while True:
            try:
                # ---- WAITING phase (animated)
                end = time.time() + interval
                last_check = 0
                while time.time() < end:
                    draw_waiting(anim, log, end, commits, pushes,
                                 branch, interval, do_push, dry_run,
                                 time.time() - t0)
                    time.sleep(1 / WAITING_FPS)

                    # every ~3s, peek at status without leaving the animation
                    if time.time() - last_check >= 3:
                        last_check = time.time()
                        s = get_status()
                        if s:
                            break   # exit wait early

                # ---- WORK phase
                committed, pushed = process_once(
                    do_push, dry_run, log, spinner, anim,
                    branch, interval, commits, pushes, t0)
                if committed: commits += 1
                if pushed:    pushes += 1

                # brief pause so user can read the result
                if committed or pushed:
                    time.sleep(2)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                log.add("error", f"{type(e).__name__}: {e}")
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        clear_line()
        print()
        print(c("═" * 66, C.GREY))
        print(c("  stopped.", C.YELLOW, bold=True))
        print(f"  runtime : {int(time.time()-t0)}s")
        print(f"  commits : {c(commits, C.MAGENTA, bold=True)}")
        print(f"  pushes  : {c(pushes, C.CYAN, bold=True)}")
        print(c("═" * 66, C.GREY))
        print()


# ================================================================
#  CLI
# ================================================================

def main():
    enable_ansi()

    ap = argparse.ArgumentParser()
    ap.add_argument("--once",     action="store_true")
    ap.add_argument("--no-push",  action="store_true")
    ap.add_argument("--dry-run",  action="store_true")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    args = ap.parse_args()

    if not is_repo():
        print(c(f"Not a git repository: {REPO_ROOT}", C.RED, bold=True))
        print(c("Run: git init", C.YELLOW))
        return 1

    log = EventLog()
    spinner = Spinner()

    if args.once or args.dry_run:
        render_header(current_branch(), args.interval,
                      not args.no_push, args.dry_run, 0, 0, 0)
        process_once(not args.no_push, args.dry_run, log, spinner,
                     WaitingAnimator(), current_branch(), args.interval,
                     0, 0, time.time())
        print()
        print(c("  done.", C.GREEN, bold=True))
        return 0

    watch(args.interval, do_push=not args.no_push, dry_run=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
