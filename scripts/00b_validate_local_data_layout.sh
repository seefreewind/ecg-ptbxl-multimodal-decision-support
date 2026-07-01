#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.data.validate_local_data_layout \
  --config configs/data_ptbxl.yaml
