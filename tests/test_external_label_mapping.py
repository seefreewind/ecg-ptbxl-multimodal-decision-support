from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "source_dataset",
    "source_label",
    "source_label_description",
    "mapped_ptbxl_superclass",
    "mapping_confidence",
    "include_in_main_external_validation",
    "include_in_sensitivity_analysis",
    "exclude_from_external_validation",
    "reason",
    "notes",
}


def test_external_label_mapping_table_contains_required_fields() -> None:
    audit = pd.read_csv("tables/table_external_label_mapping_audit.csv")

    assert REQUIRED_COLUMNS.issubset(audit.columns)
    assert {"CPSC2018", "Chapman-Shaoxing"}.issubset(set(audit["source_dataset"]))


def test_low_confidence_labels_are_excluded_from_main_external_validation() -> None:
    audit = pd.read_csv("tables/table_external_label_mapping_audit.csv")
    low = audit[audit["mapping_confidence"].isin(["low", "exclude"])]

    assert len(low) > 0
    assert not low["include_in_main_external_validation"].astype(bool).any()
    assert low["exclude_from_external_validation"].astype(bool).all()


def test_norm_only_high_confidence_subset_is_allowed_if_justified() -> None:
    audit = pd.read_csv("tables/table_external_label_mapping_audit.csv")
    norm = audit[
        audit["mapped_ptbxl_superclass"].eq("NORM")
        & audit["mapping_confidence"].eq("high")
        & audit["include_in_main_external_validation"].astype(bool)
    ]

    assert len(norm) >= 1
    assert norm["reason"].str.contains("normal", case=False).any()
