from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_signal_attribution_outputs_heatmap_source_and_leads() -> None:
    assert Path("results/xai/signal_attribution_values.npz").exists()
    summary = pd.read_csv("results/xai/signal_case_attribution_summary.csv")
    leads = pd.read_csv("tables/table_signal_lead_importance.csv")
    assert len(summary) > 0
    assert {"ecg_id", "top_signal_leads", "method"}.issubset(summary.columns)
    assert {"ecg_id", "lead", "importance_score", "rank"}.issubset(leads.columns)
    assert leads["rank"].max() == 12
