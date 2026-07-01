from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_ptbxl_ecgdeli_direct_discrepancy_diagnosis_outputs_family_summary() -> None:
    path = Path("tables/table_ptbxl_ecgdeli_direct_discrepancy_by_family.csv")
    summary = Path("results/stage14i_ptbxl_ecgdeli_direct_discrepancy_diagnosis_summary.md")
    assert path.exists()
    assert summary.exists()

    table = pd.read_csv(path)
    assert {"base_feature", "summary_statistic", "n_features", "median_mean_abs_error"}.issubset(table.columns)
    assert table["base_feature"].nunique() >= 10
    assert table["summary_statistic"].isin(["mean", "iqr", "count"]).all()


def test_ptbxl_ecgdeli_direct_discrepancy_diagnosis_keeps_recipe_blocked() -> None:
    decision = pd.read_csv("tables/table_ptbxl_ecgdeli_direct_discrepancy_decision.csv")
    row = decision.iloc[0]
    assert not bool(row["direct_420_exact_enough_for_recipe_claim"])
    assert not bool(row["can_run_multimodal_external_validation"])
    assert "direct_feature_numeric_discrepancy" in str(row["blocking_issue"])
