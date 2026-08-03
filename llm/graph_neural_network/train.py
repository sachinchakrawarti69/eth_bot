"""Train an asset-relationship GNN from node, edge, and target arrays."""
import argparse
from pathlib import Path
import numpy as np
from llm.graph_neural_network.models import build_gnn
from llm.graph_neural_network.config import CONFIG
from llm.shared import Trainer
def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("data_dir",type=Path); parser.add_argument("--resume",action="store_true"); args=parser.parse_args(); d=args.data_dir
    nodes=np.load(d / "nodes_train.npy"); model=build_gnn(CONFIG, nodes.shape[1]); trainer=Trainer(model,"storage/models/graph_neural_network",mixed_precision=True)
    trainer.fit([nodes,np.load(d / "edges_train.npy")],np.load(d / "y_train.npy"),[np.load(d / "nodes_validation.npy"),np.load(d / "edges_validation.npy")],np.load(d / "y_validation.npy"),resume=args.resume)
if __name__ == "__main__": main()
