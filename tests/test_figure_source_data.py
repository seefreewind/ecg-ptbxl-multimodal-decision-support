from __future__ import annotations

import pandas as pd


def test_fig2_performance_long_contains_main_models() -> None:
    df = pd.read_csv("figures/source_data/fig2_model_performance_long.csv")
    expected = {"strong_signal_only", "signal_embedding_mlp", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"}
    assert expected.issubset(set(df["model_name"]))
    assert {"AUROC", "average_precision", "F1", "Brier", "ECE"}.issubset(set(df["metric"]))


def test_fig5_uncertainty_has_all_coverage_levels() -> None:
    df = pd.read_csv("figures/source_data/fig5_uncertainty_risk_coverage.csv")
    coverages = {round(float(v), 1) for v in df["coverage"].unique()}
    assert {1.0, 0.9, 0.8, 0.7, 0.6, 0.5}.issubset(coverages)
    assert set(df["cutoff_source"]) == {"validation"}


def test_late_probability_concat_is_supplementary() -> None:
    df = pd.read_csv("figures/source_data/fig2_model_performance_long.csv")
    late = df[df["model_name"].eq("late_probability_concat")]
    assert len(late) > 0
    assert not late["is_main_model"].astype(bool).any()
