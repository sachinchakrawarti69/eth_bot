"""
reorganize_scripts.py -- move every script into a subfolder.

Moves:
    fetch_*.py, update_*.py       ->  fetchers/
    build_features.py, compute_sr.py,
    statistical_mode.py           ->  builders/
    opportunity.py, ml_plan.py    ->  signals/
    backtest_features.py          ->  backtest/
    export_options.py             ->  exports/

Rewrites imports and renames references throughout the repo.

Run:
    python reorganize_scripts.py
"""

from __future__ import annotations
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SP   = ROOT / "scripts_python"


# ================================================================
#  MOVE MAP
# ================================================================

MOVES = {
    # source (at scripts_python/)          -> destination (relative to scripts_python/)
    "fetch_futures.py":         "fetchers/futures.py",
    "fetch_funding.py":         "fetchers/funding.py",
    "fetch_oi.py":              "fetchers/oi.py",
    "fetch_ls_ratio.py":        "fetchers/ls_ratio.py",
    "fetch_taker.py":           "fetchers/taker.py",
    "fetch_options.py":         "fetchers/options.py",
    "fetch_intraday.py":        "fetchers/intraday.py",
    "update_multi.py":          "fetchers/multi.py",
    "update_market.py":         "fetchers/market.py",

    "build_features.py":        "builders/features.py",
    "compute_sr.py":            "builders/sr.py",
    "statistical_mode.py":      "builders/stats.py",

    "opportunity.py":           "signals/opportunity.py",
    "ml_plan.py":               "signals/ml_plan.py",

    "backtest_features.py":     "backtest/features.py",

    "export_options.py":        "exports/options.py",
}


# ================================================================
#  IMPORT REWRITES
# ================================================================
# old module path -> new module path (used inside .py files)

IMPORT_MAP = {
    "scripts_python.fetchers.futures":     "scripts_python.fetchers.futures",
    "scripts_python.fetchers.funding":     "scripts_python.fetchers.funding",
    "scripts_python.fetchers.oi":          "scripts_python.fetchers.oi",
    "scripts_python.fetchers.ls_ratio":    "scripts_python.fetchers.ls_ratio",
    "scripts_python.fetchers.taker":       "scripts_python.fetchers.taker",
    "scripts_python.fetchers.options":     "scripts_python.fetchers.options",
    "scripts_python.fetchers.intraday":    "scripts_python.fetchers.intraday",
    "scripts_python.fetchers.multi":      "scripts_python.fetchers.multi",
    "scripts_python.fetchers.market":     "scripts_python.fetchers.market",

    "scripts_python.builders.features":    "scripts_python.builders.features",
    "scripts_python.builders.sr":        "scripts_python.builders.sr",
    "scripts_python.builders.stats":  "scripts_python.builders.stats",

    "scripts_python.signals.opportunity":       "scripts_python.signals.opportunity",
    "scripts_python.signals.ml_plan":           "scripts_python.signals.ml_plan",

    "scripts_python.backtest.features": "scripts_python.backtest.features",

    "scripts_python.exports.options":    "scripts_python.exports.options",
}

# also plain module (no leading package)
PLAIN_IMPORT_MAP = {
    "fetch_futures":     "fetchers.futures",
    "fetch_funding":     "fetchers.funding",
    "fetch_oi":          "fetchers.oi",
    "fetch_ls_ratio":    "fetchers.ls_ratio",
    "fetch_taker":       "fetchers.taker",
    "fetch_options":     "fetchers.options",
    "fetch_intraday":    "fetchers.intraday",
    "update_multi":      "fetchers.multi",
    "update_market":     "fetchers.market",
    "build_features":    "builders.features",
    "compute_sr":        "builders.sr",
    "statistical_mode":  "builders.stats",
    "opportunity":       "signals.opportunity",
    "ml_plan":           "signals.ml_plan",
    "backtest_features": "backtest.features",
    "export_options":    "exports.options",
}


# ================================================================
#  COMMAND STRING REWRITES
# ================================================================
# things like "-m scripts_python.fetchers.futures" in docs / bat / scripts

COMMAND_MAP = {
    "scripts_python.fetchers.futures":     "scripts_python.fetchers.futures",
    "scripts_python.fetchers.funding":     "scripts_python.fetchers.funding",
    "scripts_python.fetchers.oi":          "scripts_python.fetchers.oi",
    "scripts_python.fetchers.ls_ratio":    "scripts_python.fetchers.ls_ratio",
    "scripts_python.fetchers.taker":       "scripts_python.fetchers.taker",
    "scripts_python.fetchers.options":     "scripts_python.fetchers.options",
    "scripts_python.fetchers.intraday":    "scripts_python.fetchers.intraday",
    "scripts_python.fetchers.multi":      "scripts_python.fetchers.multi",
    "scripts_python.fetchers.market":     "scripts_python.fetchers.market",

    "scripts_python.builders.features":    "scripts_python.builders.features",
    "scripts_python.builders.sr":        "scripts_python.builders.sr",
    "scripts_python.builders.stats":  "scripts_python.builders.stats",

    "scripts_python.signals.opportunity":       "scripts_python.signals.opportunity",
    "scripts_python.signals.ml_plan":           "scripts_python.signals.ml_plan",

    "scripts_python.backtest.features": "scripts_python.backtest.features",

    "scripts_python.exports.options":    "scripts_python.exports.options",
}


# ================================================================
#  HELPERS
# ================================================================

def section(msg):
    print()
    print("=" * 66)
    print("  " + msg)
    print("=" * 66)


def ensure_package(dir_path):
    """Create __init__.py in a folder if missing."""
    p = dir_path / "__init__.py"
    if not p.exists():
        p.touch()
        print("  + " + str(p.relative_to(ROOT)))
    else:
        print("  ok " + str(p.relative_to(ROOT)))


def move_file(src, dst):
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        print("  skip " + str(src.relative_to(ROOT)) + " (missing)")
        return False
    if dst.exists():
        print("  skip " + str(dst.relative_to(ROOT)) + " (dest exists)")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    print("  -> " + str(src.relative_to(ROOT)) + "  →  " + str(dst.relative_to(ROOT)))
    return True


def rewrite_py_imports(path):
    """Rewrite import paths in one .py file."""
    txt = path.read_text(encoding="utf-8")
    original = txt

    # full package paths
    for old, new in IMPORT_MAP.items():
        txt = txt.replace(old, new)

    # plain module names inside from ... import ...
    for old, new in PLAIN_IMPORT_MAP.items():
        # from scripts_python import fetchers.futures
        txt = re.sub(
            r"(from\s+scripts_python\s+import\s+)" + re.escape(old) + r"\b",
            r"\1" + new.replace(".", "_DOT_").replace("_DOT_", "."),
            txt)
        # from scripts_python.fetch_X import ... (already handled above)
        # from .fetch_X import  →  from .fetchers.futures import
        txt = re.sub(
            r"(from\s+\.\s*)" + re.escape(old) + r"\b",
            r"\1" + new, txt)
        # import scripts_python.fetch_X
        txt = txt.replace(
            "import scripts_python." + old,
            "import scripts_python." + new)

    if txt != original:
        path.write_text(txt, encoding="utf-8")
        return True
    return False


def rewrite_any_text(path):
    """Rewrite command strings in .md, .bat, .ps1, .txt, .yaml, .json."""
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return False
    original = txt

    for old, new in COMMAND_MAP.items():
        txt = txt.replace(old, new)

    if txt != original:
        path.write_text(txt, encoding="utf-8")
        return True
    return False


# ================================================================
#  MAIN
# ================================================================

def main():
    print("=" * 66)
    print("  REORGANIZE SCRIPTS_PYTHON")
    print("=" * 66)
    print("  root: " + str(ROOT))

    # ------------------------------------------------------------
    section("1. create subfolders + __init__.py")
    # ------------------------------------------------------------
    subs = ["fetchers", "builders", "signals", "backtest", "exports"]
    for s in subs:
        d = SP / s
        d.mkdir(parents=True, exist_ok=True)
        ensure_package(d)

    # make sure cmd/, gui/, web/ have __init__.py
    for s in ["cmd", "gui", "web"]:
        d = SP / s
        if d.exists():
            ensure_package(d)

    # ------------------------------------------------------------
    section("2. move files")
    # ------------------------------------------------------------
    moved = 0
    for src_name, dst_rel in MOVES.items():
        src = SP / src_name
        dst = SP / dst_rel
        if move_file(src, dst):
            moved += 1
    print()
    print("  moved " + str(moved) + " files")

    # ------------------------------------------------------------
    section("3. rewrite Python imports")
    # ------------------------------------------------------------
    py_files = list(ROOT.rglob("*.py"))
    rewritten = 0
    for p in py_files:
        if "__pycache__" in str(p):
            continue
        if rewrite_py_imports(p):
            print("  updated " + str(p.relative_to(ROOT)))
            rewritten += 1
    print()
    print("  rewrote " + str(rewritten) + " files")

    # ------------------------------------------------------------
    section("4. rewrite command strings in docs/bat/ps1")
    # ------------------------------------------------------------
    text_exts = {".md", ".bat", ".ps1", ".txt", ".yaml", ".yml", ".json", ".toml"}
    text_rewritten = 0
    for p in ROOT.rglob("*"):
        if p.suffix not in text_exts:
            continue
        if "__pycache__" in str(p):
            continue
        if "node_modules" in str(p):
            continue
        if rewrite_any_text(p):
            print("  updated " + str(p.relative_to(ROOT)))
            text_rewritten += 1
    print()
    print("  rewrote " + str(text_rewritten) + " files")

    # ------------------------------------------------------------
    section("5. clear caches")
    # ------------------------------------------------------------
    n = 0
    for d in list(ROOT.rglob("__pycache__")):
        try:
            shutil.rmtree(d, ignore_errors=True)
            n += 1
        except Exception:
            pass
    print("  removed " + str(n) + " __pycache__ folders")

    # ------------------------------------------------------------
    section("6. verify all imports")
    # ------------------------------------------------------------
    sys.path.insert(0, str(ROOT))
    import importlib

    modules = [
        "scripts_python.fetchers.multi",
        "scripts_python.fetchers.market",
        "scripts_python.fetchers.futures",
        "scripts_python.fetchers.funding",
        "scripts_python.fetchers.oi",
        "scripts_python.fetchers.ls_ratio",
        "scripts_python.fetchers.taker",
        "scripts_python.fetchers.options",
        "scripts_python.fetchers.intraday",
        "scripts_python.builders.features",
        "scripts_python.builders.sr",
        "scripts_python.builders.stats",
        "scripts_python.signals.opportunity",
        "scripts_python.signals.ml_plan",
        "scripts_python.backtest.features",
        "scripts_python.exports.options",
        "scripts_python.cmd.take_trade",
        "scripts_python.gui.take_trade",
        "scripts_python.web.api",
    ]

    ok = 0
    fails = []
    for mod in modules:
        try:
            importlib.import_module(mod)
            print("  ok   " + mod)
            ok += 1
        except Exception as e:
            print("  FAIL " + mod + "  →  " + type(e).__name__ + ": " + str(e)[:70])
            fails.append(mod)

    print()
    print("  " + str(ok) + "/" + str(len(modules)) + " imports work")

    # ------------------------------------------------------------
    section("7. final tree")
    # ------------------------------------------------------------
    for p in sorted(SP.rglob("*")):
        if "__pycache__" in str(p):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if p.is_dir():
            print("  " + rel + "/")
        elif p.suffix == ".py":
            print("    " + p.name)

    # ------------------------------------------------------------
    section("DONE")
    print("  Files moved : " + str(moved))
    print("  Files edited: " + str(rewritten + text_rewritten))
    print()
    if fails:
        print("  FAILED IMPORTS:")
        for f in fails:
            print("    " + f)
        print()
        print("  Install missing deps or check the error above.")
    else:
        print("  All imports work. Delete this script:")
        print("    Remove-Item reorganize_scripts.py")
    print()
    print("  New commands:")
    for old, new in COMMAND_MAP.items():
        print(f"    python -m {new}")
    print()


if __name__ == "__main__":
    main()