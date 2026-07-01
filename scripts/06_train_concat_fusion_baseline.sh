#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.train_concat_fusion \
  --config configs/model_concat_fusion.yaml
