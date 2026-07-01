#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.data.discover_data_paths \
  --config configs/data_ptbxl.yaml
