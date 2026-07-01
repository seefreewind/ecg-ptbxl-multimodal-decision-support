from __future__ import annotations

import pandas as pd


def test_dca_by_label_contains_five_labels_and_main_models() -> None:
    by_label = pd.read_csv("results/dca/dca_results_by_label.csv")
    assert {"NORM", "MI", "STTC", "CD", "HYP"}.issubset(set(by_label["label"]))
    assert {"strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"}.issubset(set(by_label["model_name"]))


def test_macro_dca_contains_main_models() -> None:
    macro = pd.read_csv("results/dca/dca_results_macro.csv")
    assert {"strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"}.issubset(set(macro["model_name"]))
    assert {"macro_net_benefit", "macro_net_benefit_vs_treat_all", "macro_net_benefit_vs_treat_none"}.issubset(macro.columns)


def test_dca_bootstrap_ci_exists_for_required_thresholds() -> None:
    ci = pd.read_csv("tables/table_dca_bootstrap_ci.csv")
    assert {0.1, 0.2, 0.3, 0.4}.issubset({round(float(v), 1) for v in ci["threshold"]})
    assert {"macro_net_benefit", "macro_net_benefit_vs_treat_all", "macro_net_benefit_vs_treat_none"}.issubset(set(ci["metric"]))
