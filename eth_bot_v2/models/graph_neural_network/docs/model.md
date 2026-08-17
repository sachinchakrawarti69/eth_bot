# Model

Graph convolution averages transformed neighbour states. Graph attention instead computes masked `softmax(QKᵀ/√d)` edge weights, allowing the model to emphasize changing cross-asset relationships.
