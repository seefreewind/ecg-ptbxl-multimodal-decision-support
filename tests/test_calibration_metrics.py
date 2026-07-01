from __future__ import annotations

import numpy as np


def test_brier_and_ece_are_bounded() -> None:
    from src.evaluation.calibration import calibration_binary

    y_true = np.array([1, 0, 1, 0])
    y_prob = np.array([0.9, 0.2, 0.7, 0.1])
    result = calibration_binary(y_true, y_prob, n_bins=2)

    assert round(result.brier, 4) == 0.0375
    assert 0.0 <= result.ece <= 1.0
    assert 0.0 <= result.mce <= 1.0


def test_multilabel_calibration_has_per_class_metrics() -> None:
    from src.evaluation.calibration import multilabel_calibration_metrics

    y_true = np.array([[1, 0], [0, 1], [1, 1]])
    y_prob = np.array([[0.8, 0.2], [0.3, 0.7], [0.6, 0.9]])
    out = multilabel_calibration_metrics(y_true, y_prob, ["A", "B"], n_bins=3)

    assert {"macro_brier", "macro_ece", "macro_mce"}.issubset(out)
    assert {"classwise_brier_A", "classwise_ece_A", "classwise_brier_B", "classwise_ece_B"}.issubset(out)
