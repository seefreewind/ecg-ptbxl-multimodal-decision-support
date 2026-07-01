from __future__ import annotations

import numpy as np


def test_entropy_outputs_nonnegative() -> None:
    from src.evaluation.uncertainty import binary_entropy

    entropy = binary_entropy(np.array([0.1, 0.5, 0.9]))
    assert np.all(entropy >= 0)
    assert entropy[1] > entropy[0]


def test_margin_uncertainty_larger_is_more_uncertain() -> None:
    from src.evaluation.uncertainty import compute_uncertainty_scores

    prob = np.array([[0.5, 0.9], [0.1, 0.9]])
    thresholds = np.array([0.5, 0.5])
    scores = compute_uncertainty_scores(prob, thresholds, labels=["A", "B"])

    assert scores.loc[0, "margin_uncertainty"] > scores.loc[1, "margin_uncertainty"]
    assert "confidence_from_margin_uncertainty" in scores.columns
