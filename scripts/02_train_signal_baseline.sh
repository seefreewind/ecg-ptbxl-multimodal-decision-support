#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.train_signal \
  --config configs/model_signal_resnet.yaml
