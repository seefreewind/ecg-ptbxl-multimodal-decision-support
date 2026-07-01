from __future__ import annotations

import numpy as np


def test_evaluator_outputs_consistent_schema() -> None:
    from src.evaluation.evaluator import evaluate_multilabel_predictions

    y_true = np.array([[1, 0], [0, 1], [1, 1]])
    y_prob = np.array([[0.9, 0.2], [0.1, 0.8], [0.7, 0.6]])

    out = evaluate_multilabel_predictions(y_true, y_prob, label_names=["A", "B"], split_name="val", model_name="m")

    assert list(out.columns) == [
        "model",
        "split",
        "label",
        "threshold",
        "auroc",
        "average_precision",
        "f1",
        "micro_f1",
        "sensitivity",
        "specificity",
        "balanced_accuracy",
        "brier_score",
        "ece",
        "positive_count",
    ]
    assert set(out["label"]) == {"macro", "A", "B"}

