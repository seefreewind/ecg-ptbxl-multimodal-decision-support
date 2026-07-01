from __future__ import annotations

import numpy as np
import pandas as pd


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]


def test_exported_prediction_with_logits_schema_and_sigmoid() -> None:
    path = "results/internal/fair_concat/fair_concat_test_predictions_with_logits.csv"
    frame = pd.read_csv(path)

    assert {"ecg_id", "split"}.issubset(frame.columns)
    assert all(f"y_true_{label}" in frame.columns for label in LABELS)
    assert all(f"logit_{label}" in frame.columns for label in LABELS)
    assert all(f"prob_{label}" in frame.columns for label in LABELS)
    for label in LABELS:
        expected = 1.0 / (1.0 + np.exp(-frame[f"logit_{label}"]))
        assert np.allclose(expected, frame[f"prob_{label}"], atol=1e-6)


def test_exported_prediction_row_counts_match_splits() -> None:
    val = pd.read_csv("results/internal/gated_fusion/gated_fusion_val_predictions_with_logits.csv")
    test = pd.read_csv("results/internal/gated_fusion/gated_fusion_test_predictions_with_logits.csv")
    assert len(val) == 2183
    assert len(test) == 2198
    assert set(val["split"]) == {"val"}
    assert set(test["split"]) == {"test"}
