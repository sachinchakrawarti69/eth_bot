"""Train a TCN from standard NumPy arrays."""
import argparse
from pathlib import Path
from models.temporal_convolutional_network.models import build_tcn
from models.temporal_convolutional_network.config import CONFIG
from models.shared.core import train_from_numpy
def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("data_dir",type=Path); parser.add_argument("--resume",action="store_true"); args=parser.parse_args()
    train_from_numpy(build_tcn, CONFIG, args.data_dir, "storage/models/temporal_convolutional_network", resume=args.resume)
if __name__ == "__main__": main()
