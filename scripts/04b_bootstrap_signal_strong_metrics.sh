#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" -m src.training.bootstrap_signal_metrics \
  --val-predictions "${VAL_PREDICTIONS:-results/internal/signal_strong/signal_strong_val_predictions.csv}" \
  --test-predictions "${TEST_PREDICTIONS:-results/internal/signal_strong/signal_strong_test_predictions.csv}" \
  --output-csv results/internal/signal_strong_bootstrap_ci.csv \
  --table-csv tables/table_signal_strong_bootstrap_ci.csv \
  --n-bootstrap "${N_BOOTSTRAP:-1000}"
