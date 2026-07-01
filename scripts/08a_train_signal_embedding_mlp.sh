#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.train_ablation_mlp \
  --config configs/model_signal_embedding_mlp.yaml
