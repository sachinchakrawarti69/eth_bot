"""Train TFT quantile forecasts from standard NumPy arrays."""
import argparse
from pathlib import Path
from llm.temporal_fusion_transformer.models import build_tft
from llm.temporal_fusion_transformer.config import CONFIG
from llm.shared.core import train_from_numpy
def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("data_dir",type=Path); parser.add_argument("--resume",action="store_true"); args=parser.parse_args()
    train_from_numpy(build_tft, CONFIG, args.data_dir, "storage/models/temporal_fusion_transformer", resume=args.resume)
if __name__ == "__main__": main()
