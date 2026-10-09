"""Ready-made commit message generator.

Standalone use:
    python commit_messages.py                    # preview current changes
    python commit_messages.py --subject          # just the subject line
    python commit_messages.py --json             # JSON output
    python commit_messages.py --test             # run self-tests

Import use:
    from commit_messages import build_message, classify_path
    msg = build_message([("M", "scripts_python/fetch_futures.py")])
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ================================================================
#  CONFIG
# ================================================================

REPO_ROOT       = Path(__file__).resolve().parent
MAX_SUBJECT_LEN = 72
MAX_BODY_FILES  = 20
MAX_EMOJI       = True


# ================================================================
#  FILE CATEGORIES
# ================================================================

CATEGORY_RULES = [
    # (prefix, category) — first match wins
    ("eth_bot_v2/database/schema/",          "schema"),
    ("eth_bot_v2/database/",                 "db"),
    ("eth_bot_v2/scripts_python/fetch_",     "fetch"),
    ("eth_bot_v2/scripts_python/build_",     "feature"),
    ("eth_bot_v2/scripts_python/compute_",   "indicator"),
    ("eth_bot_v2/scripts_python/statistical_", "stats"),
    ("eth_bot_v2/scripts_python/backtest",   "backtest"),
    ("eth_bot_v2/scripts_python/opportunity", "signal"),
    ("eth_bot_v2/scripts_python/web/",       "web"),
    ("eth_bot_v2/scripts_python/",           "scripts"),
    ("eth_bot_v2/excel/",                    "excel"),
    ("eth_bot_v2/analysis/",                 "analysis"),
    ("eth_bot_v2/reports_pkg/",              "reports"),
    ("eth_bot_v2/web/",                      "web"),
    ("eth_bot_v2/docs/",                     "docs"),
    ("eth_bot_v2/reports/",                  "output"),
    ("eth_bot_v2/exports/",                  "output"),
    ("eth_bot_v2/engine/",                   "engine"),
    ("eth_bot_v2/models/",                   "models"),
]


# ================================================================
#  CATEGORY METADATA
# ================================================================

CATEGORY_META = {
    "fetch":     {"verb": "update fetchers",    "emoji": "📡", "color": "\033[36m"},
    "feature":   {"verb": "update features",    "emoji": "🔢", "color": "\033[35m"},
    "indicator": {"verb": "update indicators",  "emoji": "📊", "color": "\033[34m"},
    "stats":     {"verb": "update statistics",  "emoji": "📈", "color": "\033[32m"},
    "backtest":  {"verb": "update backtest",    "emoji": "🎯", "color": "\033[33m"},
    "signal":    {"verb": "update signals",     "emoji": "🚦", "color": "\033[31m"},
    "schema":    {"verb": "update schema",      "emoji": "🗄",  "color": "\033[34m"},
    "db":        {"verb": "update database",    "emoji": "💾", "color": "\033[33m"},
    "scripts":   {"verb": "update scripts",     "emoji": "⚙",  "color": "\033[37m"},
    "excel":     {"verb": "update excel",       "emoji": "📗", "color": "\033[32m"},
    "analysis":  {"verb": "update analysis",    "emoji": "🔍", "color": "\033[35m"},
    "reports":   {"verb": "update reports",     "emoji": "📄", "color": "\033[34m"},
    "web":       {"verb": "update web ui",      "emoji": "🌐", "color": "\033[36m"},
    "docs":      {"verb": "update docs",        "emoji": "📚", "color": "\033[33m"},
    "engine":    {"verb": "update engine",      "emoji": "🏭", "color": "\033[31m"},
    "models":    {"verb": "update models",      "emoji": "🧠", "color": "\033[35m"},
    "output":    {"verb": "update outputs",     "emoji": "📦", "color": "\033[90m"},
    "code":      {"verb": "update code",        "emoji": "💻", "color": "\033[37m"},
    "test":      {"verb": "update tests",       "emoji": "🧪", "color": "\033[32m"},
    "config":    {"verb": "update config",      "emoji": "⚙",  "color": "\033[37m"},
    "ci":        {"verb": "update ci",          "emoji": "🔧", "color": "\033[36m"},
    "other":     {"verb": "update files",       "emoji": "📝", "color": "\033[37m"},
}


# ================================================================
#  STATUS ICONS
# ================================================================

STATUS_META = {
    "M":  {"verb": "modify",  "icon": "✏",  "color": "\033[33m"},
    "A":  {"verb": "add",     "icon": "➕", "color": "\033[32m"},
    "D":  {"verb": "delete",  "icon": "🗑",  "color": "\033[31m"},
    "R":  {"verb": "rename",  "icon": "↻",  "color": "\033[36m"},
    "C":  {"verb": "copy",    "icon": "📋", "color": "\033[36m"},
    "??": {"verb": "add",     "icon": "➕", "color": "\033[32m"},
    "T":  {"verb": "chtype",  "icon": "🔀", "color": "\033[35m"},
    "U":  {"verb": "update",  "icon": "⬆",  "color": "\033[35m"},
}


# ================================================================
#  SPECIAL FILE HANDLERS
# ================================================================
# Specific files get hand-crafted messages instead of the generic form.

SPECIAL_FILES = {
    "requirements.txt":      "update dependencies",
    "package.json":          "update npm dependencies",
    "package-lock.json":     "update npm lockfile",
    "pyproject.toml":        "update project config",
    "setup.py":              "update package config",
    ".gitignore":            "update gitignore",
    "README.md":             "update readme",
    "Dockerfile":            "update dockerfile",
    "docker-compose.yml":    "update docker compose",
}


# ================================================================
#  CLASSIFIER
# ================================================================

def classify_path(path: str) -> str:
    """Map a file path to a category."""
    p = path.lower().replace("\\", "/")

    # specific rules first
    for prefix, cat in CATEGORY_RULES:
        if p.startswith(prefix):
            # refine further
            return refine_category(cat, p)

    # generic fallback by extension
    if p.endswith(".md"):                          return "docs"
    if p.endswith((".xlsx", ".csv", ".json", ".png",
                   ".jpg", ".svg", ".pdf")):      return "output"
    if p.endswith((".py", ".ipynb", ".sql",
                   ".yaml", ".yml", ".toml",
                   ".js", ".jsx", ".ts", ".tsx")): return "code"
    if "test" in Path(p).name:                     return "test"
    if "config" in Path(p).name:                   return "config"
    if p.endswith((".lock", ".cfg", ".ini")):      return "config"

    return "other"


def refine_category(cat: str, path: str) -> str:
    """Further specialize a category based on filename."""
    name = Path(path).name.lower()
    if "test" in name:                return "test"
    if name.endswith(".sql"):         return "schema"
    if name.endswith((".yml", ".yaml", ".toml", ".ini", ".cfg")):
        return "config"
    return cat


# ================================================================
#  FILENAME -> WORDS
# ================================================================

def filename_to_words(name: str) -> str:
    """'build_features.py' -> 'build features'."""
    stem = Path(name).stem
    words = re.sub(r"[_\-]+", " ", stem).strip().lower()
    return words


# ================================================================
#  SUBJECT LINE
# ================================================================

def make_subject(changes: list[tuple[str, str]], emoji: bool = MAX_EMOJI) -> str:
    """Build just the first line."""
    if not changes:
        return ""

    by_cat: dict[str, list[tuple[str, str]]] = {}
    for status, path in changes:
        cat = classify_path(path)
        by_cat.setdefault(cat, []).append((status, path))

    dominant_cat = max(by_cat, key=lambda k: len(by_cat[k]))
    meta = CATEGORY_META.get(dominant_cat, CATEGORY_META["other"])
    icon = meta["emoji"] + " " if emoji else ""

    n = len(changes)

    # ---- single file
    if n == 1:
        status, path = changes[0]
        name = Path(path).name
        smeta = STATUS_META.get(status, STATUS_META["M"])
        # check for special file
        if name in SPECIAL_FILES:
            return f"{icon}{SPECIAL_FILES[name]}"
        # single file, use verb + filename
        words = filename_to_words(name)
        return f"{icon}{smeta['verb']} {words}"

    # ---- all changes are the same status
    statuses = {s for s, _ in changes}
    if len(statuses) == 1:
        status = statuses.pop()
        smeta = STATUS_META.get(status, STATUS_META["M"])

        # if all adds, use "add"
        if status in ("A", "??"):
            # list a few names
            names = [filename_to_words(Path(p).name) for _, p in changes[:3]]
            if len(changes) == 2:
                s = f"{icon}add {names[0]} and {names[1]}"
            elif len(changes) == 3:
                s = f"{icon}add {names[0]}, {names[1]}, and {names[2]}"
            else:
                s = f"{icon}add {n} new files"
            if len(s) > MAX_SUBJECT_LEN:
                s = f"{icon}add {n} new files"
            return s

        if status == "D":
            names = [filename_to_words(Path(p).name) for _, p in changes[:3]]
            if len(changes) <= 3:
                s = f"{icon}delete " + ", ".join(names)
            else:
                s = f"{icon}delete {n} files"
            return s

    # ---- multiple categories → use dominant verb + count
    subj = f"{icon}{meta['verb']}"

    # append detail if only a few files
    highlights = []
    for status, path in changes[:MAX_BODY_FILES]:
        name = Path(path).name
        if name.endswith(".pyc") or "__pycache__" in path:
            continue
        words = filename_to_words(name)
        if words and words not in highlights:
            highlights.append(words)

    if 2 <= len(highlights) <= 3:
        s = f"{icon}{meta['verb']}: " + ", ".join(highlights)
        if len(s) <= MAX_SUBJECT_LEN:
            return s

    s = f"{icon}{meta['verb']} ({n} files)"
    if len(s) > MAX_SUBJECT_LEN:
        s = s[:MAX_SUBJECT_LEN - 3].rstrip() + "..."
    return s


# ================================================================
#  FULL BODY
# ================================================================

def make_body(changes: list[tuple[str, str]]) -> str:
    """Body with grouped file list."""
    by_cat: dict[str, list[tuple[str, str]]] = {}
    for status, path in changes:
        cat = classify_path(path)
        by_cat.setdefault(cat, []).append((status, path))

    lines = []

    for cat in sorted(by_cat, key=lambda k: -len(by_cat[k])):
        meta = CATEGORY_META.get(cat, CATEGORY_META["other"])
        files = by_cat[cat]
        lines.append(f"## {meta['emoji']} {cat} ({len(files)})")
        for status, path in files[:MAX_BODY_FILES]:
            smeta = STATUS_META.get(status, STATUS_META["M"])
            short = path
            if short.startswith("eth_bot_v2/"):
                short = short[len("eth_bot_v2/"):]
            lines.append(f"  {smeta['icon']} {short}")
        if len(files) > MAX_BODY_FILES:
            lines.append(f"  … and {len(files) - MAX_BODY_FILES} more")
        lines.append("")

    lines.append(f"generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return "\n".join(lines)


# ================================================================
#  MAIN ENTRY
# ================================================================

def build_message(changes: list[tuple[str, str]], emoji: bool = MAX_EMOJI) -> str:
    """Full commit message: subject + blank + body."""
    if not changes:
        return ""
    subject = make_subject(changes, emoji=emoji)
    body    = make_body(changes)
    return subject + "\n\n" + body


def build_json(changes: list[tuple[str, str]], emoji: bool = MAX_EMOJI) -> dict:
    """Structured form."""
    by_cat: dict[str, list] = {}
    for status, path in changes:
        cat = classify_path(path)
        by_cat.setdefault(cat, []).append({"status": status, "path": path})
    return {
        "subject":    make_subject(changes, emoji=emoji),
        "body":       make_body(changes),
        "n_files":    len(changes),
        "categories": {k: len(v) for k, v in by_cat.items()},
        "files":      [{"status": s, "path": p} for s, p in changes],
        "generated":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ================================================================
#  STANDALONE — read git status itself
# ================================================================

def git_status() -> list[tuple[str, str]]:
    """Read git status from REPO_ROOT."""
    r = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return []
    out = r.stdout
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
#  TESTS
# ================================================================

def run_tests() -> int:
    cases = [
        ([("M", "eth_bot_v2/scripts_python/fetch_futures.py")],
         "should be 'modify fetch futures'"),

        ([("A", "eth_bot_v2/scripts_python/build_features.py"),
          ("A", "eth_bot_v2/scripts_python/compute_sr.py")],
         "should add 2 files"),

        ([("D", "eth_bot_v2/database/market.db")],
         "should delete market db"),

        ([("M", "eth_bot_v2/excel/export_ohlcv.py"),
          ("M", "eth_bot_v2/excel/export_forecasts.py"),
          ("M", "eth_bot_v2/excel/export_multi.py")],
         "should be excel exports with file names"),

        ([("M", "eth_bot_v2/web/trade_desk.html"),
          ("M", "eth_bot_v2/scripts_python/web/api.py"),
          ("M", "eth_bot_v2/scripts_python/opportunity.py")],
         "mixed categories"),

        ([("??", "eth_bot_v2/docs/cmd/cmd.md")],
         "add cmd md (docs)"),

        ([("M", "requirements.txt")],
         "update dependencies"),

        ([("M", "eth_bot_v2/database/schema/0019_trade_setups.sql")],
         "modify trade setups sql (schema)"),
    ]

    print("=" * 70)
    print("  COMMIT MESSAGE TESTS")
    print("=" * 70)
    print()

    failed = 0
    for i, (changes, expect) in enumerate(cases, 1):
        subj = make_subject(changes, emoji=False)
        ok = "✓" if subj else "✗"
        if not subj:
            failed += 1
        print(f"  {ok} [{i}] {subj}")
        print(f"      expect: {expect}")
        print()

    print("=" * 70)
    print(f"  {len(cases) - failed}/{len(cases)} passed")
    print("=" * 70)
    return 0 if failed == 0 else 1


# ================================================================
#  CLI
# ================================================================

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", action="store_true",
                    help="print only the subject line")
    ap.add_argument("--json", action="store_true",
                    help="output JSON instead of plain text")
    ap.add_argument("--no-emoji", action="store_true",
                    help="plain text messages, no emoji")
    ap.add_argument("--test", action="store_true",
                    help="run self-tests")
    args = ap.parse_args()

    if args.test:
        return run_tests()

    changes = git_status()

    if not changes:
        print("no changes")
        return 0

    emoji = not args.no_emoji

    if args.json:
        print(json.dumps(build_json(changes, emoji=emoji), indent=2, ensure_ascii=False))
        return 0

    if args.subject:
        print(make_subject(changes, emoji=emoji))
        return 0

    print(build_message(changes, emoji=emoji))
    return 0


if __name__ == "__main__":
    sys.exit(main())