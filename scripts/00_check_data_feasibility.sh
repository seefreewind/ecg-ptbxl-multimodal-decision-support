#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.data.check_data_feasibility \
  --config configs/data_ptbxl.yaml
