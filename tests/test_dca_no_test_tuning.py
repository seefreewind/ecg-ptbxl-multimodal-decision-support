from __future__ import annotations

import numpy as np
import pandas as pd


def test_retained_dca_uses_validation_selected_uncertainty_cutoffs() -> None:
    cutoffs = pd.read_csv("results/uncertainty/triage_cutoffs_validation.csv")
    retained = pd.read_csv("results/dca/dca_results_retained_80_coverage.csv")

    validation_cutoffs = cutoffs[
        cutoffs["probability_mode"].eq("temperature_scaled")
        & cutoffs["uncertainty_score"].eq("entropy_macro")
        & np.isclose(cutoffs["coverage"], 0.8)
    ]

    assert {"strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"}.issubset(
        set(validation_cutoffs["model_name"])
    )
    assert set(retained["analysis_subset"]) == {"retained_80_coverage"}
    assert {"strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"}.issubset(
        set(retained["model_name"])
    )


def test_dca_thresholds_are_evaluation_grid_not_tuned_classification_thresholds() -> None:
    grid = pd.read_csv("results/dca/dca_threshold_grid.csv")

    assert grid["threshold"].between(0, 1, inclusive="neither").all()
    assert np.isclose(grid["threshold"].min(), 0.01)
    assert np.isclose(grid["threshold"].max(), 0.50)
    assert {"0.01_to_0.50", "0.05_to_0.40", "0.10_to_0.30"}.issubset(set(grid["grid_name"]))
