from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_external_ecgdeli_prototype_outputs_are_guarded() -> None:
    audit_path = Path("tables/table_external_ecgdeli_feature_prototype_audit.csv")
    summary_path = Path("results/stage14e_external_ecgdeli_feature_prototype_summary.md")
    assert audit_path.exists()
    assert summary_path.exists()

    audit = pd.read_csv(audit_path)
    assert {"cpsc2018", "chapman"}.issubset(set(audit["dataset"]))
    assert "schema_exact_match" in audit.columns
    assert not audit["schema_exact_match"].astype(bool).any()
    assert "ptbxl_plus_exact_531_recipe_missing" in set(audit["blocking_issue"])


def test_external_ecgdeli_prototype_feature_files_are_exploratory() -> None:
    for dataset in ["cpsc2018", "chapman"]:
        path = Path(f"data/processed/external/{dataset}_ecgdeli_features_prototype.csv")
        assert path.exists()
        df = pd.read_csv(path)
        assert {"record_id", "source_dataset"}.issubset(df.columns)
        assert len(df.columns) < 533
