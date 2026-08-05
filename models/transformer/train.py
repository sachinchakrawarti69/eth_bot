"""Train a time-series Transformer using the standard NumPy data contract."""
import argparse
from pathlib import Path
from models.shared.core import train_from_numpy
from models.transformer.config import CONFIG
from models.transformer.models import build_transformer
def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("data_dir", type=Path); parser.add_argument("--resume", action="store_true"); args=parser.parse_args()
    train_from_numpy(build_transformer, CONFIG, args.data_dir, "storage/models/transformer", resume=args.resume)
if __name__ == "__main__": main()
