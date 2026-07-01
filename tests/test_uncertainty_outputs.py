from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_uncertainty_output_schema_is_stable() -> None:
    table = pd.read_csv("tables/table_uncertainty_triage.csv")
    required = {
        "model_name",
        "probability_mode",
        "uncertainty_score",
        "split",
        "coverage",
        "cutoff_source",
        "uncertainty_cutoff",
        "retained_n",
        "referred_n",
        "referral_fraction",
        "retained_macro_auroc",
        "retained_macro_f1",
        "retained_brier",
        "retained_ece",
    }
    assert required.issubset(table.columns)


def test_test_evaluation_uses_validation_cutoff_source() -> None:
    test = pd.read_csv("results/uncertainty/risk_coverage_metrics_test.csv")
    assert set(test["cutoff_source"]) == {"validation"}


def test_uncertainty_summary_exists_after_stage10() -> None:
    assert Path("results/uncertainty/summary.md").exists()
