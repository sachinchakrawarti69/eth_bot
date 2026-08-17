# Graph Neural Network

The GNN models relationships between ETH and related assets. Inputs are node features `(batch, assets, features)` and edge adjacency/features `(batch, assets, assets)`; the output is a graph-level next-candle forecast. Run `python -m llm.graph_neural_network.train DATA_DIR`.

Graph convolutions spread neighbour information; graph attention learns which relationships matter. Results depend strongly on sound, time-safe edge construction and the selected asset universe.
