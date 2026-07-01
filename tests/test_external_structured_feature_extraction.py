from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_external_structured_extraction_audit_has_required_columns() -> None:
    table = pd.read_csv("tables/table_external_structured_feature_extraction_audit.csv")
    assert {"cpsc2018", "chapman"}.issubset(set(table["dataset"]))
    assert {
        "required_feature_count",
        "exact_ptbxl_plus_feature_match",
        "can_run_full_multimodal_external_validation",
        "blocking_issue",
    }.issubset(table.columns)
    assert (table["required_feature_count"] == 531).all()


def test_multimodal_external_validation_requires_exact_feature_match() -> None:
    table = pd.read_csv("tables/table_external_structured_feature_extraction_audit.csv")
    blocked = table[~table["exact_ptbxl_plus_feature_match"].astype(bool)]
    assert not blocked["can_run_full_multimodal_external_validation"].astype(bool).any()
    assert blocked["blocking_issue"].replace("", pd.NA).notna().all()


def test_external_structured_feature_templates_are_empty_and_schema_stable() -> None:
    columns = Path("data/processed/external/external_structured_feature_template_columns.txt")
    assert columns.exists()
    assert len([line for line in columns.read_text().splitlines() if line.strip()]) == 531
    for dataset in ["cpsc2018", "chapman"]:
        path = Path(f"data/processed/external/{dataset}_structured_features_template.csv")
        assert path.exists()
        df = pd.read_csv(path)
        assert df.empty
        assert {"record_id", "source_dataset"}.issubset(df.columns)
