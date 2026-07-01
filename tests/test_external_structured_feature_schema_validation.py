from __future__ import annotations

import pandas as pd


def test_external_structured_schema_validation_outputs_decision() -> None:
    table = pd.read_csv("tables/table_external_structured_feature_schema_validation.csv")
    assert {"cpsc2018", "chapman"}.issubset(set(table["dataset"]))
    assert {
        "schema_exact_match",
        "nonempty",
        "can_run_multimodal_external_validation",
        "blocking_issue",
    }.issubset(table.columns)


def test_empty_templates_do_not_enable_multimodal_external_validation() -> None:
    table = pd.read_csv("tables/table_external_structured_feature_schema_validation.csv")
    blocked = table[~table["nonempty"].astype(bool)]
    if not blocked.empty:
        assert not blocked["can_run_multimodal_external_validation"].astype(bool).any()
        assert blocked["blocking_issue"].str.contains("empty|missing", regex=True).all()
