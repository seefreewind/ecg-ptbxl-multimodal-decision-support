#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.features.build_fusion_dataset \
  --config configs/fair_fusion_dataset.yaml
