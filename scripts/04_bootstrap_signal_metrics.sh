#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.bootstrap_signal_metrics \
  --val-predictions results/internal/signal_val_predictions.csv \
  --test-predictions results/internal/signal_test_predictions.csv \
  --output-csv results/internal/signal_bootstrap_ci.csv \
  --table-csv tables/table_signal_bootstrap_ci.csv \
  --n-bootstrap "${N_BOOTSTRAP:-500}"
