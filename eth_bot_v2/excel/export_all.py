"""Run every Excel export in one command.

    python -m excel.export_all
"""
from __future__ import annotations
import time


def main():
    print("=" * 60)
    print("  EXCEL EXPORT - ALL")
    print("=" * 60)

    tasks = [
        ("OHLCV",     "excel.export_ohlcv"),
        ("Forecasts", "excel.export_forecasts"),
    ]

    results = []
    for name, mod in tasks:
        print()
        print(f"[{name}]")
        t0 = time.time()
        try:
            m = __import__(mod, fromlist=["build"])
            m.build()
            results.append((name, "OK", time.time() - t0))
        except Exception as e:
            print(f"  FAIL: {type(e).__name__}: {e}")
            results.append((name, f"FAIL: {e}", time.time() - t0))

    print()
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for name, status, secs in results:
        mark = "OK  " if status == "OK" else "FAIL"
        print(f"  [{mark}] {name:<12} {secs:.2f}s  {status}")
    print("=" * 60)


if __name__ == "__main__":
    main()
