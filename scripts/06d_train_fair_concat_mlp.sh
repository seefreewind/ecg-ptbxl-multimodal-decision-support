#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.train_fair_concat_fusion \
  --config configs/model_fair_concat_mlp.yaml
