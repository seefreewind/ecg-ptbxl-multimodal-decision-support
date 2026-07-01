from __future__ import annotations

import numpy as np


def test_threshold_tuning_uses_only_supplied_validation_arrays() -> None:
    from src.training.thresholds import apply_thresholds, tune_per_class_thresholds

    y_true_val = np.array([[1, 0], [1, 0], [0, 1], [0, 1]])
    y_prob_val = np.array([[0.8, 0.2], [0.7, 0.3], [0.4, 0.9], [0.3, 0.8]])

    thresholds = tune_per_class_thresholds(y_true_val, y_prob_val, label_names=["A", "B"])
    pred = apply_thresholds(y_prob_val, thresholds)

    assert set(thresholds) == {"A", "B"}
    assert pred.shape == y_true_val.shape


def test_apply_thresholds_requires_matching_class_count() -> None:
    from src.training.thresholds import apply_thresholds

    y_prob = np.array([[0.2, 0.8]])

    try:
        apply_thresholds(y_prob, np.array([0.5]))
    except ValueError as exc:
        assert "Threshold count" in str(exc)
    else:
        raise AssertionError("Expected threshold shape validation to fail.")

