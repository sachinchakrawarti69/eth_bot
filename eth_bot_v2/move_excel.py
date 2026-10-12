"""
move_excel.py

Actions:
  1. move excel/ -> scripts_python/excel/
  2. rename scripts_python/ -> scripts/
  3. rewrite every import inside .py files (from excel.X -> from scripts.excel.X)
  4. rewrite command strings in .md / .bat / .ps1 / .json / .txt
  5. delete old __pycache__
  6. verify imports
  7. print final tree

Run:
    python move_excel.py
"""

from __future__ import annotations
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OLD_SCRIPTS = ROOT / "scripts_python"
NEW_SCRIPTS = ROOT / "scripts"
OLD_EXCEL   = ROOT / "excel"
NEW_EXCEL   = NEW_SCRIPTS / "excel"


# ================================================================
#  IMPORT REWRITE MAPS
# ================================================================

# 1. inside .py files: "scripts_python." -> "scripts."
PACKAGE_RENAME = [
    ("scripts_python.", "scripts."),
    ("from scripts_python ", "from scripts "),
    ("import scripts_python", "import scripts"),
    ("scripts_python/", "scripts/"),
    ("scripts_python\\", "scripts\\"),
]

# 2. excel package import rewrites
EXCEL_IMPORTS = [
    ("from excel.",         "from scripts.excel."),
    ("from excel ",         "from scripts.excel "),
    ("import excel\n",      "import scripts.excel\n"),
    ("import excel.",       "import scripts.excel."),
]

# 3. command strings in docs / bat / ps1
COMMANDS = [
    ("python -m excel.export_all",          "python -m scripts.excel.export_all"),
    ("python -m excel.export_ohlcv",        "python -m scripts.excel.export_ohlcv"),
    ("python -m excel.export_forecasts",    "python -m scripts.excel.export_forecasts"),
    ("python -m excel.export_multi",        "python -m scripts.excel.export_multi"),
    ("python -m excel.export_indicators",   "python -m scripts.excel.export_indicators"),
    ("excel\\export_all.py",                "scripts\\excel\\export_all.py"),
    ("excel/export_all.py",                 "scripts/excel/export_all.py"),
    ("from excel.common import",            "from scripts.excel.common import"),
    ("from excel import",                   "from scripts.excel import"),
    ("scripts_python",                      "scripts"),
]


# ================================================================
#  HELPERS
# ================================================================

def section(msg):
    print()
    print("=" * 66)
    print("  " + msg)
    print("=" * 66)


def ensure_init(p: Path):
    if not p.exists():
        p.touch()
        print("  + " + str(p.relative_to(ROOT)))


def rewrite_py_imports(path: Path) -> bool:
    """Rewrite imports in one .py file."""
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return False
    orig = txt

    # package rename
    for old, new in PACKAGE_RENAME:
        txt = txt.replace(old, new)

    # excel imports
    for old, new in EXCEL_IMPORTS:
        txt = txt.replace(old, new)

    if txt != orig:
        path.write_text(txt, encoding="utf-8")
        return True
    return False


def rewrite_text(path: Path) -> bool:
    """Rewrite command strings in non-python files."""
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return False
    orig = txt

    for old, new in COMMANDS:
        txt = txt.replace(old, new)

    if txt != orig:
        path.write_text(txt, encoding="utf-8")
        return True
    return False


# ================================================================
#  MAIN
# ================================================================

def main():
    print("=" * 66)
    print("  MOVE EXCEL INTO SCRIPTS + RENAME PACKAGE")
    print("=" * 66)
    print("  root: " + str(ROOT))

    # ------------------------------------------------------------
    section("0. safety check")
    # ------------------------------------------------------------
    if not OLD_SCRIPTS.exists():
        print("  ERROR: " + str(OLD_SCRIPTS) + " not found.")
        print("  Nothing to do.")
        return 1
    if not OLD_EXCEL.exists():
        print("  WARNING: " + str(OLD_EXCEL) + " not found (already moved?)")
    if NEW_SCRIPTS.exists() and NEW_SCRIPTS != OLD_SCRIPTS:
        print("  WARNING: " + str(NEW_SCRIPTS) + " already exists.")
        print("  Will merge contents if safe.")

    # ------------------------------------------------------------
    section("1. rename scripts_python/ -> scripts/")
    # ------------------------------------------------------------
    if OLD_SCRIPTS.exists() and not NEW_SCRIPTS.exists():
        OLD_SCRIPTS.rename(NEW_SCRIPTS)
        print("  scripts_python/ -> scripts/")
    elif OLD_SCRIPTS.exists() and NEW_SCRIPTS.exists():
        print("  both exist — skipping rename, will merge")
    elif NEW_SCRIPTS.exists():
        print("  already named scripts/")
    else:
        print("  ERROR: no scripts folder")

    # ------------------------------------------------------------
    section("2. move excel/ into scripts/excel/")
    # ------------------------------------------------------------
    if OLD_EXCEL.exists():
        # remove any old copy first
        if NEW_EXCEL.exists():
            shutil.rmtree(NEW_EXCEL, ignore_errors=True)
        shutil.move(str(OLD_EXCEL), str(NEW_EXCEL))
        print("  excel/ -> scripts/excel/")
    else:
        print("  excel/ not at top level (already moved?)")

    # ensure __init__.py exists
    if NEW_EXCEL.exists():
        ensure_init(NEW_EXCEL / "__init__.py")

    # ------------------------------------------------------------
    section("3. ensure scripts/ is a package")
    # ------------------------------------------------------------
    ensure_init(NEW_SCRIPTS / "__init__.py")

    # ------------------------------------------------------------
    section("4. rewrite imports in all .py files")
    # ------------------------------------------------------------
    n_py = 0
    for p in ROOT.rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        if rewrite_py_imports(p):
            print("  updated " + str(p.relative_to(ROOT)))
            n_py += 1
    print()
    print("  " + str(n_py) + " .py files updated")

    # ------------------------------------------------------------
    section("5. rewrite commands in docs / bat / ps1")
    # ------------------------------------------------------------
    exts = {".md", ".bat", ".ps1", ".txt", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini"}
    n_txt = 0
    for p in ROOT.rglob("*"):
        if p.suffix not in exts:
            continue
        if "__pycache__" in str(p):
            continue
        if "node_modules" in str(p):
            continue
        if rewrite_text(p):
            print("  updated " + str(p.relative_to(ROOT)))
            n_txt += 1
    print()
    print("  " + str(n_txt) + " text files updated")

    # ------------------------------------------------------------
    section("6. clear all __pycache__")
    # ------------------------------------------------------------
    n = 0
    for d in list(ROOT.rglob("__pycache__")):
        try:
            shutil.rmtree(d, ignore_errors=True)
            n += 1
        except Exception:
            pass
    print("  removed " + str(n) + " cache folders")

    # ------------------------------------------------------------
    section("7. verify imports")
    # ------------------------------------------------------------
    sys.path.insert(0, str(ROOT))
    import importlib

    modules = [
        # fetchers
        "scripts.fetchers.multi",
        "scripts.fetchers.market",
        "scripts.fetchers.futures",
        "scripts.fetchers.funding",
        "scripts.fetchers.oi",
        "scripts.fetchers.ls_ratio",
        "scripts.fetchers.taker",
        "scripts.fetchers.options",
        "scripts.fetchers.intraday",
        # builders
        "scripts.builders.features",
        "scripts.builders.sr",
        "scripts.builders.stats",
        # signals
        "scripts.signals.opportunity",
        "scripts.signals.ml_plan",
        # backtest
        "scripts.backtest.features",
        # exports
        "scripts.exports.options",
        # excel
        "scripts.excel.common",
        "scripts.excel.export_all",
        "scripts.excel.export_ohlcv",
        "scripts.excel.export_forecasts",
        "scripts.excel.export_multi",
        "scripts.excel.export_indicators",
        # cmd / gui / web
        "scripts.cmd.take_trade",
        "scripts.gui.take_trade",
        "scripts.web.api",
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
            fails.append((mod, e))

    print()
    print("  " + str(ok) + "/" + str(len(modules)) + " imports work")

    # ------------------------------------------------------------
    section("8. final tree")
    # ------------------------------------------------------------
    for p in sorted(NEW_SCRIPTS.rglob("*")):
        if "__pycache__" in str(p):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if p.is_dir():
            print("  " + rel + "/")
        elif p.suffix == ".py":
            print("    " + p.name)

    # ------------------------------------------------------------
    section("DONE")
    print("  py files rewritten  : " + str(n_py))
    print("  text files updated  : " + str(n_txt))
    print()
    if fails:
        print("  FAILED IMPORTS:")
        for m, e in fails:
            print("    " + m)
            print("      " + type(e).__name__ + ": " + str(e))
        print()
        print("  Fix the errors above, then rerun this script.")
    else:
        print("  All imports OK.")
        print()
        print("  New command paths:")
        print("    python -m scripts.fetchers.multi")
        print("    python -m scripts.builders.features")
        print("    python -m scripts.signals.opportunity")
        print("    python -m scripts.excel.export_all")
        print()
        print("  Delete this script:")
        print("    Remove-Item move_excel.py")
    print()


if __name__ == "__main__":
    main()