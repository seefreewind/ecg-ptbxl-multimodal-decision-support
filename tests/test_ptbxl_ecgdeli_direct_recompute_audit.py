from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_ptbxl_ecgdeli_direct_recompute_audit_outputs_comparisons() -> None:
    candidate_path = Path("data/processed/ptbxl_ecgdeli_direct_recomputed_sample.csv")
    comparison_path = Path("tables/table_ptbxl_ecgdeli_direct_recompute_comparison.csv")
    summary_path = Path("results/stage14h_ptbxl_ecgdeli_direct_recompute_audit_summary.md")
    assert candidate_path.exists()
    assert comparison_path.exists()
    assert summary_path.exists()

    candidates = pd.read_csv(candidate_path)
    comparison = pd.read_csv(comparison_path)
    assert len(candidates) >= 3
    assert {"ecg_id", "record_id", "source_dataset"}.issubset(candidates.columns)
    assert comparison["feature"].nunique() == 420
    assert comparison["n_pairs"].astype(int).sum() > 0


def test_ptbxl_ecgdeli_direct_recompute_does_not_unlock_external_multimodal() -> None:
    decision = pd.read_csv("tables/table_ptbxl_ecgdeli_direct_recompute_decision.csv")
    row = decision.iloc[0]
    assert not bool(row["can_claim_exact_ptbxl_plus_recipe"])
    assert not bool(row["can_run_multimodal_external_validation"])
    assert "ptbxl_plus_exact_531_recipe_missing" in str(row["blocking_issue"])
