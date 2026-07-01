#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.train_signal \
  --config "${CONFIG:-configs/model_signal_resnet_strong.yaml}"

