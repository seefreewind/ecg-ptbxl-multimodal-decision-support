from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_missing_external_data_discovery_outputs_stable_rows() -> None:
    candidates = pd.read_csv("results/external/external_dataset_candidates.csv")

    assert {"cpsc2018", "chapman"}.issubset(set(candidates["dataset_candidate"]))
    assert {
        "dataset_candidate",
        "root_path",
        "n_waveform_files",
        "n_metadata_files",
        "n_label_files",
        "status",
        "notes",
    }.issubset(candidates.columns)
    assert Path("results/external/external_dataset_discovery_report.md").exists()


def test_external_readiness_summary_is_generated() -> None:
    summary = Path("results/stage13a_external_readiness_summary.md")

    assert summary.exists()
    text = summary.read_text()
    assert "Stage 13A External Validation Readiness Summary" in text
    assert "No formal external validation was run" in text
