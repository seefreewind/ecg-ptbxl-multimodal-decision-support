#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.features.extract_signal_embeddings \
  --config configs/extract_signal_embeddings.yaml
