from __future__ import annotations

import pandas as pd


def test_reliability_source_schema() -> None:
    from src.evaluation.reliability import confidence_histogram_source, reliability_curve_source

    predictions = pd.DataFrame(
        {
            "A_true": [1, 0, 1],
            "A_prob": [0.9, 0.2, 0.7],
            "B_true": [0, 1, 1],
            "B_prob": [0.1, 0.8, 0.6],
        }
    )
    reliability = reliability_curve_source(predictions, ["A", "B"], "model", "test", "raw", n_bins=3)
    histogram = confidence_histogram_source(predictions, ["A", "B"], "model", "test", "raw", n_bins=3)

    assert {"model_name", "split", "calibration_mode", "label", "bin", "confidence", "accuracy", "count"}.issubset(
        reliability.columns
    )
    assert {"model_name", "split", "calibration_mode", "label", "bin", "bin_left", "bin_right", "count"}.issubset(
        histogram.columns
    )
    assert set(reliability["label"]) == {"A", "B"}
