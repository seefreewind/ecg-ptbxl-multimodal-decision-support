#!/usr/bin/env bash
set -e

set +e
"${PYTHON:-python3}" -m src.data.prepare_ptbxl \
  --config configs/data_ptbxl.yaml
PTBXL_STATUS=$?
set -e

"${PYTHON:-python3}" -m src.data.prepare_ptbxl_plus \
  --config configs/data_ptbxl.yaml

exit ${PTBXL_STATUS}
