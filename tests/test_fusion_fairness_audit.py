from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_fusion_fairness_audit_archives_late_probability_concat() -> None:
    audit = Path("results/stage6a_fusion_fairness_audit.md")
    assert audit.exists()
    text = audit.read_text(encoding="utf-8")
    assert "late-probability concat baseline" in text
    assert "five signal probability features" in text


def test_fusion_comparison_marks_fairness_if_present() -> None:
    path = Path("tables/table_fusion_baseline_fairness_comparison.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    late = df[df["model"].eq("late-probability concat")].iloc[0]
    fair = df[df["model"].eq("fair MLP-concat")].iloc[0]
    assert late["is_fair_comparator_for_gated"] == "no"
    assert "5 signal probabilities" in late["reason"]
    assert fair["is_fair_comparator_for_gated"] == "yes"
    assert fair["classifier_type"] == "MLP head"
