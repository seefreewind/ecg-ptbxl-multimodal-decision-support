#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.train_gated_fusion \
  --config configs/model_gated_fusion.yaml
