from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_ptbxl_plus_feature_description_audit_documents_unresolved_families() -> None:
    audit_path = Path("tables/table_ptbxl_plus_feature_description_unresolved_audit.csv")
    summary_path = Path("results/stage14j_ptbxl_plus_feature_description_audit_summary.md")
    assert audit_path.exists()
    assert summary_path.exists()

    audit = pd.read_csv(audit_path)
    assert {
        "ptbxl_plus_feature",
        "base_feature",
        "derivability",
        "description_id",
        "ecgdeli_feature",
        "description_found",
    }.issubset(audit.columns)
    assert len(audit) == 111
    assert {"QT_IntCorr", "P_Morph", "ST_Elev", "HA_"}.issubset(set(audit["base_feature"]))
    assert audit["description_found"].any()
    assert audit.loc[audit["base_feature"].eq("HA_"), "description_found"].all()


def test_ptbxl_plus_feature_description_audit_keeps_external_multimodal_blocked() -> None:
    decision = pd.read_csv("tables/table_ptbxl_plus_feature_description_decision.csv")
    row = decision.iloc[0]
    assert not bool(row["can_generate_exact_531_features"])
    assert not bool(row["can_run_multimodal_external_validation"])
    assert "direct_feature_numeric_discrepancy" in str(row["blocking_issue"])
    assert "ptbxl_plus_exact_531_recipe_missing" in str(row["blocking_issue"])
