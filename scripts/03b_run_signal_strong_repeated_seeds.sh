#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.run_signal_repeated \
  --config "${CONFIG:-configs/model_signal_resnet_strong.yaml}" \
  --seeds "${SEEDS:-2026,2027,2028}" \
  --output-dir results/internal/signal_strong_repeated

