from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_unified_explanation_contains_structured_and_signal_summaries() -> None:
    unified = pd.read_csv("results/xai/unified_case_explanations.csv")
    assert len(unified) > 0
    assert {"top_structured_features", "top_signal_leads", "gate_signal", "gate_structured"}.issubset(unified.columns)
    assert unified["top_structured_features"].notna().all()
    assert unified["top_signal_leads"].notna().all()


def test_stage11_summary_exists() -> None:
    assert Path("results/stage11_xai_summary.md").exists()
