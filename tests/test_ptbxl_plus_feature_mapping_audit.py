from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_ptbxl_plus_feature_mapping_audit_outputs_all_required_features() -> None:
    mapping_path = Path("tables/table_ptbxl_plus_ecgdeli_feature_mapping_audit.csv")
    summary_path = Path("results/stage14f_ptbxl_plus_feature_mapping_audit_summary.md")
    assert mapping_path.exists()
    assert summary_path.exists()

    mapping = pd.read_csv(mapping_path)
    assert len(mapping) == 531
    assert mapping["ptbxl_plus_feature"].is_unique
    assert {"direct_ecgdeli", "requires_extra_formula", "requires_morphology_function", "unknown_recipe"}.issubset(
        set(mapping["derivability"])
    )


def test_ptbxl_plus_feature_mapping_keeps_external_multimodal_blocked() -> None:
    decision = pd.read_csv("tables/table_ptbxl_plus_ecgdeli_feature_mapping_decision.csv")
    row = decision.iloc[0]
    assert not bool(row["can_generate_exact_531_features"])
    assert not bool(row["can_run_multimodal_external_validation"])
    assert "ptbxl_plus_exact_531_recipe_missing" in str(row["blocking_issue"])
