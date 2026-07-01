#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.data.validate_ptbxl_plus \
  --config configs/data_ptbxl.yaml
