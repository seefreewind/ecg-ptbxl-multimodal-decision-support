#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.data.align_ptbxl_plus \
  --config configs/data_ptbxl.yaml
