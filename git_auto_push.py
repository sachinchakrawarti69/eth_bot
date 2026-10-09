"""Git auto-commit and push with smart messages.

Watches the repo. On every change:
  1. detects added / modified / deleted files
  2. builds a meaningful commit message from the paths + change types
  3. commits and pushes

Run:
    python git_auto_push.py                    # watch mode (Ctrl+C to stop)
    python git_auto_push.py --once             # single pass, then exit
    python git_auto_push.py --no-push          # commit but don't push
    python git_auto_push.py --interval 15      # poll every 15s (default 30)
    python git_auto_push.py --dry-run          # show what WOULD happen
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ================================================================
#  CONFIG
# ================================================================

REPO_ROOT = Path(__file__).resolve().parent

DEFAULT_INTERVAL = 30          # seconds between polls
MAX_SUBJECT_LEN  = 72          # first line of commit message
MAX_BODY_FILES   = 20          # how many files to list in the body


# ================================================================
#  GIT WRAPPER
# ================================================================

def git(*args, check=True, capture=True):
    """Run a git command. Returns stdout as string."""
    cmd = ["git"] + list(args)
    r = subprocess.run(
        cmd, cwd=str(REPO_ROOT),
        capture_output=capture, text=True,
        encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {err}")
    return (r.stdout or "").strip()


def is_repo() -> bool:
    try:
        git("rev-parse", "--is-inside-work-tree")
        return True
    except Exception:
        return False


def has_remote() -> bool:
    try:
        return bool(git("remote", "get-url", "origin"))
    except Exception:
        return False


def current_branch() -> str:
    try:
        return git("rev-parse", "--abbrev-ref", "HEAD")
    except Exception:
        return "main"


# ================================================================
#  CHANGE DETECTION
# ================================================================

def get_status() -> list[tuple[str, str]]:
    """
    Return a list of (status, path).
    status is one of: M (modified), A (added), D (deleted),
                      R (renamed), ?? (untracked)
    """
    out = git("status", "--porcelain=v1", "-z")
    if not out:
        return []
    # porcelain -z: entries separated by NUL, rename entries have two paths
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
        # renames have old + new path separated by NUL
        if code[0] == "R":
            new_path = parts[i+1] if i+1 < len(parts) else ""
            result.append(("R", f"{path} -> {new_path}"))
            i += 2
        else:
            result.append((code.strip() or "??", path))
            i += 1
    return result


def classify_path(path: str) -> str:
    """Map a file path to a coarse category for the commit message."""
    p = path.lower().replace("\\", "/")

    if p.startswith("eth_bot_v2/database/"):
        return "db"
    if p.startswith("eth_bot_v2/scripts_python/fetch_"):
        return "fetch"
    if p.startswith("eth_bot_v2/scripts_python/"):
        return "scripts"
    if p.startswith("eth_bot_v2/excel/"):
        return "excel"
    if p.startswith("eth_bot_v2/analysis/"):
        return "analysis"
    if p.startswith("eth_bot_v2/reports_pkg/"):
        return "reports"
    if p.startswith("eth_bot_v2/web/") or p.startswith("eth_bot_v2/web\\"):
        return "web"
    if p.startswith("eth_bot_v2/docs/"):
        return "docs"
    if p.startswith("eth_bot_v2/reports/"):
        return "output"
    if p.startswith("eth_bot_v2/exports/"):
        return "output"
    if p.startswith("eth_bot_v2/database/schema/"):
        return "schema"
    if p.startswith("eth_bot_v2/"):
        return "code"

    if p.endswith(".md"):
        return "docs"
    if p.endswith((".xlsx", ".csv", ".json", ".png")):
        return "output"
    if p.endswith((".py", ".ipynb", ".sql", ".yaml", ".yml", ".toml")):
        return "code"

    return "other"


# ================================================================
#  MESSAGE BUILDER
# ================================================================

CATEGORY_VERBS = {
    "fetch":   "update fetchers",
    "scripts": "update scripts",
    "schema":  "update schema",
    "db":      "update database",
    "excel":   "update excel exports",
    "analysis":"update analysis",
    "reports": "update reports",
    "web":     "update web ui",
    "docs":    "update docs",
    "code":    "update code",
    "output":  "update outputs",
    "other":   "update files",
}

STATUS_PREFIX = {
    "M":  "modify",
    "A":  "add",
    "D":  "delete",
    "R":  "rename",
    "??": "add",
}


def filename_to_words(name: str) -> str:
    """'build_features.py' -> 'build features'."""
    stem = Path(name).stem
    return stem.replace("_", " ").replace("-", " ").strip()


def build_message(changes: list[tuple[str, str]]) -> str:
    """Return a commit message (subject + blank + body)."""
    if not changes:
        return ""

    # group files by category
    by_cat: dict[str, list[tuple[str, str]]] = {}
    for status, path in changes:
        cat = classify_path(path)
        by_cat.setdefault(cat, []).append((status, path))

    # pick the dominant category (most changes)
    dominant_cat = max(by_cat, key=lambda k: len(by_cat[k]))
    dominant_verb = CATEGORY_VERBS.get(dominant_cat, "update")

    # collect the "highlights" — the most specific filenames changed
    highlights = []
    for status, path in changes[:MAX_BODY_FILES]:
        name = Path(path).name
        if name.endswith(".pyc") or "/__pycache__/" in path:
            continue
        words = filename_to_words(name)
        prefix = STATUS_PREFIX.get(status, "change")
        highlights.append(f"{prefix} {words}")

    # ---- subject
    n = len(changes)
    if n == 1:
        status, path = changes[0]
        name = Path(path).name
        verb = STATUS_PREFIX.get(status, "update")
        subject = f"{verb} {name}"
    else:
        subject = f"{dominant_verb} ({n} files)"
        if len(highlights) <= 3:
            subject = f"{dominant_verb}: " + ", ".join(highlights)

    if len(subject) > MAX_SUBJECT_LEN:
        subject = subject[:MAX_SUBJECT_LEN - 3].rstrip() + "..."

    # ---- body
    lines = [subject, ""]

    for cat in sorted(by_cat, key=lambda k: -len(by_cat[k])):
        files = by_cat[cat]
        lines.append(f"# {cat} ({len(files)})")
        for status, path in files[:MAX_BODY_FILES]:
            status_letter = status if status in ("M", "A", "D", "R") else "?"
            short = path
            if short.startswith("eth_bot_v2/"):
                short = short[len("eth_bot_v2/"):]
            lines.append(f"  {status_letter} {short}")
        if len(files) > MAX_BODY_FILES:
            lines.append(f"  ... and {len(files) - MAX_BODY_FILES} more")
        lines.append("")

    lines.append(f"generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return "\n".join(lines)


# ================================================================
#  COMMIT + PUSH
# ================================================================

def stage_all() -> None:
    git("add", "-A")


def has_staged() -> bool:
    out = git("diff", "--cached", "--name-only")
    return bool(out.strip())


def commit(msg: str) -> bool:
    r = subprocess.run(
        ["git", "commit", "-F", "-"],
        cwd=str(REPO_ROOT),
        input=msg, text=True, encoding="utf-8",
        capture_output=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        if "nothing to commit" in err.lower():
            return False
        raise RuntimeError(f"commit failed: {err}")
    return True


def push() -> tuple[bool, str]:
    branch = current_branch()
    r = subprocess.run(
        ["git", "push", "origin", branch],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    return r.returncode == 0, out.strip()


# ================================================================
#  MAIN LOOP
# ================================================================

def process_once(do_push: bool = True, dry_run: bool = False) -> bool:
    """Detect changes, commit, push. Return True if something was done."""
    changes = get_status()
    if not changes:
        return False

    msg = build_message(changes)

    print()
    print("─" * 60)
    print(f"  {len(changes)} change(s) detected at "
          f"{datetime.now().strftime('%H:%M:%S')}")
    print("─" * 60)
    for status, path in changes[:30]:
        print(f"    {status:<3} {path}")
    if len(changes) > 30:
        print(f"    ... and {len(changes) - 30} more")
    print()
    print("  commit message:")
    for line in msg.splitlines():
        print(f"    │ {line}")
    print()

    if dry_run:
        print("  [dry-run] no commit or push")
        return True

    stage_all()
    if not has_staged():
        print("  nothing staged after add -A")
        return False

    if not commit(msg):
        print("  nothing to commit")
        return False

    print("  committed")

    if do_push:
        if not has_remote():
            print("  no remote 'origin' configured - skipping push")
            return True
        ok, out = push()
        if ok:
            print("  pushed to origin")
        else:
            print("  PUSH FAILED:")
            for line in out.splitlines()[-10:]:
                print(f"    {line}")
    else:
        print("  push skipped (--no-push)")
    return True


def watch(interval: int, do_push: bool, dry_run: bool) -> None:
    print("=" * 60)
    print("  GIT AUTO PUSH")
    print("=" * 60)
    print(f"  repo     : {REPO_ROOT}")
    print(f"  branch   : {current_branch()}")
    print(f"  interval : {interval}s")
    print(f"  push     : {do_push}")
    print(f"  dry run  : {dry_run}")
    print()
    print("  watching for changes... (Ctrl+C to stop)")
    print()

    last_state = None

    while True:
        try:
            changes = get_status()
            state = tuple(sorted(changes))

            if changes and state != last_state:
                if dry_run:
                    process_once(do_push=False, dry_run=True)
                else:
                    process_once(do_push=do_push, dry_run=False)
                last_state = tuple(sorted(get_status()))
            elif not changes:
                last_state = None
                ts = datetime.now().strftime("%H:%M:%S")
                sys.stdout.write(f"\r  [{ts}] clean - waiting...")
                sys.stdout.flush()

            time.sleep(interval)
        except KeyboardInterrupt:
            print()
            print()
            print("  stopped.")
            return
        except Exception as e:
            print()
            print(f"  error: {type(e).__name__}: {e}")
            print(f"  retrying in {interval}s...")
            time.sleep(interval)


# ================================================================
#  CLI
# ================================================================

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once",     action="store_true",
                    help="single pass, then exit")
    ap.add_argument("--no-push",  action="store_true",
                    help="commit but don't push")
    ap.add_argument("--dry-run",  action="store_true",
                    help="show changes but don't commit/push")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                    help=f"poll interval in seconds (default {DEFAULT_INTERVAL})")
    args = ap.parse_args()

    if not is_repo():
        print(f"Not a git repository: {REPO_ROOT}")
        print("Run: git init")
        return 1

    if args.once or args.dry_run:
        process_once(do_push=not args.no_push, dry_run=args.dry_run)
        return 0

    watch(args.interval, do_push=not args.no_push, dry_run=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())