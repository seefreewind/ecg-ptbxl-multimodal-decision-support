#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.bootstrap_signal_metrics \
  --val-predictions results/internal/fair_concat/fair_concat_val_predictions.csv \
  --test-predictions results/internal/fair_concat/fair_concat_test_predictions.csv \
  --output-csv results/internal/fair_concat_bootstrap_ci.csv \
  --table-csv tables/table_fair_concat_bootstrap_ci.csv \
  --labels NORM,MI,STTC,CD,HYP \
  --n-bootstrap "${N_BOOTSTRAP:-1000}" \
  --seed 2026
