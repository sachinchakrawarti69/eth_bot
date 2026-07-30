import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT))

from llm.lstm.preprocessing.merge_data import merge_all


print("=" * 70)
print("TEST MERGE DATA")
print("=" * 70)

df = merge_all()

print()

print("Shape")

print(df.shape)

print()

print("Columns")

print(df.columns.tolist())

print()

print(df.dtypes)

print()

print(df.head())

print()

print(df.tail())

print()

print(df.info())