"""Ready-made commit message generator.

Standalone use:
    python commit_messages.py
    python commit_messages.py --subject
    python commit_messages.py --json
    python commit_messages.py --no-emoji
    python commit_messages.py --test
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT       = Path(__file__).resolve().parent
MAX_SUBJECT_LEN = 72
MAX_BODY_FILES  = 20


CATEGORY_RULES = [
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


CATEGORY_META = {
    "fetch":     {"verb": "update fetchers",    "emoji": "📡"},
    "feature":   {"verb": "update features",    "emoji": "🔢"},
    "indicator": {"verb": "update indicators",  "emoji": "📊"},
    "stats":     {"verb": "update statistics",  "emoji": "📈"},
    "backtest":  {"verb": "update backtest",    "emoji": "🎯"},
    "signal":    {"verb": "update signals",     "emoji": "🚦"},
    "schema":    {"verb": "update schema",      "emoji": "🗄"},
    "db":        {"verb": "update database",    "emoji": "💾"},
    "scripts":   {"verb": "update scripts",     "emoji": "⚙"},
    "excel":     {"verb": "update excel",       "emoji": "📗"},
    "analysis":  {"verb": "update analysis",    "emoji": "🔍"},
    "reports":   {"verb": "update reports",     "emoji": "📄"},
    "web":       {"verb": "update web ui",      "emoji": "🌐"},
    "docs":      {"verb": "update docs",        "emoji": "📚"},
    "engine":    {"verb": "update engine",      "emoji": "🏭"},
    "models":    {"verb": "update models",      "emoji": "🧠"},
    "output":    {"verb": "update outputs",     "emoji": "📦"},
    "code":      {"verb": "update code",        "emoji": "💻"},
    "test":      {"verb": "update tests",       "emoji": "🧪"},
    "config":    {"verb": "update config",      "emoji": "⚙"},
    "other":     {"verb": "update files",       "emoji": "📝"},
}


STATUS_META = {
    "M":  {"verb": "modify",  "icon": "✏"},
    "A":  {"verb": "add",     "icon": "➕"},
    "D":  {"verb": "delete",  "icon": "🗑"},
    "R":  {"verb": "rename",  "icon": "↻"},
    "??": {"verb": "add",     "icon": "➕"},
}


SPECIAL_FILES = {
    "requirements.txt":   "update dependencies",
    "package.json":       "update npm dependencies",
    "package-lock.json":  "update npm lockfile",
    "pyproject.toml":     "update project config",
    "setup.py":           "update package config",
    ".gitignore":         "update gitignore",
    "README.md":          "update readme",
    "Dockerfile":         "update dockerfile",
    "docker-compose.yml": "update docker compose",
}


def classify_path(path):
    p = path.lower().replace("\\", "/")
    for prefix, cat in CATEGORY_RULES:
        if p.startswith(prefix):
            return refine_category(cat, p)
    if p.endswith(".md"):                                    return "docs"
    if p.endswith((".xlsx",".csv",".json",".png",".jpg",
                   ".svg",".pdf")):                          return "output"
    if p.endswith((".py",".ipynb",".sql",".yaml",".yml",
                   ".toml",".js",".jsx",".ts",".tsx")):      return "code"
    if "test" in Path(p).name:                               return "test"
    if "config" in Path(p).name:                             return "config"
    if p.endswith((".lock",".cfg",".ini")):                  return "config"
    return "other"


def refine_category(cat, path):
    name = Path(path).name.lower()
    if "test" in name:                          return "test"
    if name.endswith(".sql"):                   return "schema"
    if name.endswith((".yml",".yaml",".toml",
                      ".ini",".cfg")):          return "config"
    return cat


def filename_to_words(name):
    stem = Path(name).stem
    return re.sub(r"[_\-]+", " ", stem).strip().lower()


def make_subject(changes, emoji=True):
    if not changes:
        return ""
    by_cat = {}
    for status, path in changes:
        cat = classify_path(path)
        by_cat.setdefault(cat, []).append((status, path))
    dominant_cat = max(by_cat, key=lambda k: len(by_cat[k]))
    meta = CATEGORY_META.get(dominant_cat, CATEGORY_META["other"])
    icon = meta["emoji"] + " " if emoji else ""
    n = len(changes)

    if n == 1:
        status, path = changes[0]
        name = Path(path).name
        smeta = STATUS_META.get(status, STATUS_META["M"])
        if name in SPECIAL_FILES:
            return f"{icon}{SPECIAL_FILES[name]}"
        words = filename_to_words(name)
        return f"{icon}{smeta['verb']} {words}"

    statuses = {s for s, _ in changes}
    if len(statuses) == 1:
        status = statuses.pop()
        if status in ("A", "??"):
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
                return f"{icon}delete " + ", ".join(names)
            return f"{icon}delete {n} files"

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
        s = s[:MAX_SUBJECT_LEN-3].rstrip() + "..."
    return s


def make_body(changes):
    by_cat = {}
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
            lines.append(f"  ... and {len(files) - MAX_BODY_FILES} more")
        lines.append("")
    lines.append(f"generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return "\n".join(lines)


def build_message(changes, emoji=True):
    if not changes:
        return ""
    return make_subject(changes, emoji) + "\n\n" + make_body(changes)


def build_json(changes, emoji=True):
    by_cat = {}
    for status, path in changes:
        cat = classify_path(path)
        by_cat.setdefault(cat, []).append({"status": status, "path": path})
    return {
        "subject":    make_subject(changes, emoji),
        "body":       make_body(changes),
        "n_files":    len(changes),
        "categories": {k: len(v) for k, v in by_cat.items()},
        "files":      [{"status": s, "path": p} for s, p in changes],
        "generated":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def git_status():
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


def run_tests():
    cases = [
        ([("M", "eth_bot_v2/scripts_python/fetch_futures.py")],
         "modify fetch futures"),
        ([("A", "eth_bot_v2/scripts_python/build_features.py"),
          ("A", "eth_bot_v2/scripts_python/compute_sr.py")],
         "add 2 files"),
        ([("D", "eth_bot_v2/database/market.db")],
         "delete market db"),
        ([("M", "eth_bot_v2/excel/export_ohlcv.py"),
          ("M", "eth_bot_v2/excel/export_forecasts.py"),
          ("M", "eth_bot_v2/excel/export_multi.py")],
         "excel exports"),
        ([("M", "eth_bot_v2/web/trade_desk.html"),
          ("M", "eth_bot_v2/scripts_python/web/api.py"),
          ("M", "eth_bot_v2/scripts_python/opportunity.py")],
         "mixed"),
        ([("??", "eth_bot_v2/docs/cmd/cmd.md")],
         "add cmd md"),
        ([("M", "requirements.txt")],
         "update dependencies"),
        ([("M", "eth_bot_v2/database/schema/0019_trade_setups.sql")],
         "modify trade setups sql"),
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
        print(f"      ({expect})")
        print()
    print("=" * 70)
    print(f"  {len(cases)-failed}/{len(cases)} passed")
    print("=" * 70)
    return 0 if failed == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject",  action="store_true")
    ap.add_argument("--json",     action="store_true")
    ap.add_argument("--no-emoji", action="store_true")
    ap.add_argument("--test",     action="store_true")
    args = ap.parse_args()

    if args.test:
        return run_tests()

    changes = git_status()
    if not changes:
        print("no changes")
        return 0

    emoji = not args.no_emoji

    if args.json:
        print(json.dumps(build_json(changes, emoji=emoji),
                         indent=2, ensure_ascii=False))
        return 0
    if args.subject:
        print(make_subject(changes, emoji=emoji))
        return 0

    print(build_message(changes, emoji=emoji))
    return 0


if __name__ == "__main__":
    sys.exit(main())
