from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_ecgdeli_pipeline_setup_records_components() -> None:
    audit = pd.read_csv("tables/table_ecgdeli_pipeline_setup_audit.csv")
    assert {
        "ptbxl_feature_benchmark",
        "ECGdeli_MATLAB",
        "pyECGdeli",
        "MATLAB_runtime",
        "target_schema",
    }.issubset(set(audit["component"]))


def test_ecgdeli_pipeline_does_not_allow_multimodal_without_exact_generator() -> None:
    decision = pd.read_csv("tables/table_ecgdeli_pipeline_decision.csv")
    row = decision.iloc[0]
    if not bool(row["can_run_exact_external_feature_extraction"]):
        assert not bool(row["can_run_full_multimodal_external_validation"])
        assert "ptbxl_plus_exact_feature_generation_recipe_missing" in str(row["blocking_issue"])


def test_ecgdeli_pipeline_summary_generated() -> None:
    path = Path("results/stage14b_ecgdeli_pipeline_setup_summary.md")
    assert path.exists()
    text = path.read_text()
    assert "not a complete or validated PTB-XL+ 531-feature generator" in text


def test_ecgdeli_smoke_test_passed() -> None:
    smoke = pd.read_csv("tables/table_ecgdeli_smoke_test.csv")
    row = smoke.iloc[0]
    assert bool(row["passed"])
    assert int(row["fpt_multichannel_rows"]) > 0
    assert int(row["fpt_cell_leads"]) == 12
