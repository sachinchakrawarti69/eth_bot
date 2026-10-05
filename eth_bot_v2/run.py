"""Run the full pipeline: update -> export -> report.

    python run.py
"""
from __future__ import annotations
import subprocess
import sys
import time


def step(label, module):
    print()
    print("=" * 60)
    print(f"  {label}")
    print("=" * 60)
    t0 = time.time()
    rc = subprocess.call([sys.executable, "-m", module])
    secs = time.time() - t0
    mark = "OK  " if rc == 0 else f"FAIL({rc})"
    print(f"  -> {mark}  {secs:.2f}s")
    return rc == 0


def main():
    print("=" * 60)
    print("  ETH_BOT FULL PIPELINE")
    print("=" * 60)

    steps = [
        ("1/3  Update market data", "scripts_python.update_market"),
        ("2/3  Export to Excel",    "excel.export_all"),
        ("3/3  Generate report",    "reports_pkg.daily_report"),
    ]

    results = []
    for label, mod in steps:
        ok = step(label, mod)
        results.append((label, ok))
        if not ok:
            print(f"  -> stopping after failure")
            break

    print()
    print("=" * 60)
    print("  FINAL")
    print("=" * 60)
    for label, ok in results:
        print(f"  [{'OK' if ok else 'FAIL'}]  {label}")
    print("=" * 60)

    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
