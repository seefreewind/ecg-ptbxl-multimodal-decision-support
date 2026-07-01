from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_external_signal_outputs_use_signal_only_scope_if_generated() -> None:
    metrics_path = Path("results/external/external_signal_metrics.csv")
    if not metrics_path.exists():
        return
    metrics = pd.read_csv(metrics_path)
    assert set(metrics["model"]).issubset({"strong_signal_only"})
    assert set(metrics["threshold_source"]) == {"ptbxl_validation"}
    assert set(metrics["temperature_source"]) == {"ptbxl_validation"}


def test_external_signal_summary_disallows_multimodal_claim_if_generated() -> None:
    summary = Path("results/stage13b_signal_external_validation_summary.md")
    if not summary.exists():
        return
    text = summary.read_text()
    assert "signal-only external results" in text
    assert "not multimodal external validation" in text
    assert "do not establish clinical readiness" in text
