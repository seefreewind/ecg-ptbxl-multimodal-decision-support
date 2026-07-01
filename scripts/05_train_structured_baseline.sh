#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.train_structured \
  --config configs/model_structured_logistic.yaml
