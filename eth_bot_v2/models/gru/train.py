"""Train a GRU variant from saved NumPy arrays."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from models.gru.config import CONFIG
from models.gru.models import build_gru, build_stacked_gru, build_bidirectional_gru, build_attention_gru
from models.shared import Trainer

BUILDERS = {"single": build_gru, "stacked": build_stacked_gru, "bidirectional": build_bidirectional_gru, "attention": build_attention_gru}
def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("data_dir", type=Path); parser.add_argument("--variant", choices=BUILDERS, default="single"); parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(); data = args.data_dir
    trainer = Trainer(BUILDERS[args.variant](CONFIG), Path("storage/models/gru"), mixed_precision=True)
    trainer.fit(np.load(data / "x_train.npy"), np.load(data / "y_train.npy"), np.load(data / "x_validation.npy"), np.load(data / "y_validation.npy"), resume=args.resume)
if __name__ == "__main__": main()
