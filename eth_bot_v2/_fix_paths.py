"""Replace hardcoded sys.path in every notebook with a portable version."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

OLD = '''import sys
sys.path.insert(0, r"D:\\\\Projects\\\\done\\\\eth_bot\\\\eth_bot_v2")'''

NEW = '''import sys, os
from pathlib import Path
_p = Path.cwd().resolve()
while _p != _p.parent and not (_p / "database").exists():
    _p = _p.parent
sys.path.insert(0, str(_p))'''

# also handle the office PC path in case some notebooks have it
OLD_ALT = '''import sys
sys.path.insert(0, r"D:\\\\Sachin Chakrawarti\\\\eth_bot\\\\eth_bot_v2")'''


def fix_str(s):
    changed = False
    for old in (OLD, OLD_ALT):
        if old in s:
            s = s.replace(old, NEW)
            changed = True
    return s, changed


def main():
    nbs = list(ROOT.rglob("*.ipynb"))
    total = 0
    for nb in nbs:
        if ".ipynb_checkpoints" in str(nb):
            continue
        try:
            data = json.loads(nb.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  skip {nb.name}: {e}")
            continue

        changed = False
        for cell in data.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            src = "".join(cell.get("source", []))
            new, c = fix_str(src)
            if c:
                cell["source"] = new.splitlines(keepends=True)
                changed = True

        if changed:
            nb.write_text(json.dumps(data, indent=1), encoding="utf-8")
            print(f"  fixed {nb.relative_to(ROOT)}")
            total += 1

    print()
    print(f"patched {total} notebooks")


if __name__ == "__main__":
    main()