from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_ptbxl_plus_recipe_blocker_package_lists_unlock_requirements() -> None:
    package_path = Path("results/stage14k_ptbxl_plus_recipe_blocker_package.md")
    requirements_path = Path("tables/table_ptbxl_plus_recipe_unlock_requirements.csv")
    assert package_path.exists()
    assert requirements_path.exists()

    requirements = pd.read_csv(requirements_path)
    assert {"requirement", "current_evidence", "minimum_unlock_condition", "status"}.issubset(requirements.columns)
    assert len(requirements) >= 6
    assert requirements["status"].eq("blocked").all()
    assert requirements["requirement"].str.contains("numeric agreement", case=False).any()
    assert requirements["requirement"].str.contains("531", case=False).any()


def test_ptbxl_plus_recipe_blocker_package_preserves_external_gate() -> None:
    decision = pd.read_csv("tables/table_ptbxl_plus_recipe_blocker_decision.csv")
    row = decision.iloc[0]
    assert not bool(row["can_run_multimodal_external_validation"])
    assert not bool(row["can_claim_exact_ptbxl_plus_reproduction"])
    assert "direct_feature_numeric_discrepancy" in str(row["blocking_issue"])
    assert "ptbxl_plus_exact_531_recipe_missing" in str(row["blocking_issue"])
