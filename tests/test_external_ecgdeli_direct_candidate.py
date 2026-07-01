from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_external_ecgdeli_direct_candidate_tables_have_only_direct_columns() -> None:
    mapping = pd.read_csv("tables/table_ptbxl_plus_ecgdeli_feature_mapping_audit.csv")
    direct = set(mapping.loc[mapping["derivability"].eq("direct_ecgdeli"), "ptbxl_plus_feature"])
    assert len(direct) == 420

    for dataset in ["cpsc2018", "chapman"]:
        path = Path(f"data/processed/external/{dataset}_ecgdeli_direct_candidate_features.csv")
        assert path.exists()
        table = pd.read_csv(path)
        assert len(table) == 2
        assert {"record_id", "source_dataset"}.issubset(table.columns)
        feature_cols = set(table.columns) - {"record_id", "source_dataset"}
        assert feature_cols == direct
        assert table[list(feature_cols)].notna().any(axis=None)


def test_external_ecgdeli_direct_candidate_keeps_multimodal_blocked() -> None:
    decision = pd.read_csv("tables/table_external_ecgdeli_direct_candidate_decision.csv")
    row = decision.iloc[0]
    assert int(row["n_generated_direct_features"]) == 420
    assert int(row["n_missing_required_features"]) == 111
    assert not bool(row["can_run_multimodal_external_validation"])
    assert "ptbxl_plus_exact_531_recipe_missing" in str(row["blocking_issue"])

    audit = pd.read_csv("tables/table_external_ecgdeli_direct_candidate_audit.csv")
    assert set(audit["status"]) == {"generated_direct_candidate_features"}
    assert (audit["n_missing_direct_features"].astype(int) == 0).all()
