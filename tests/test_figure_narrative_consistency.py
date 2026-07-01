from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_figure_qc_report_generated_and_passed() -> None:
    assert Path("results/figure_source_data_qc_report.md").exists()
    qc = pd.read_csv("tables/table_figure_source_data_qc.csv")
    assert not qc["status"].eq("failed").any()


def test_manifest_has_no_positive_gated_superiority_claim() -> None:
    manifest = pd.read_csv("figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv")
    text = " ".join(manifest["notes"].fillna("").astype(str)).lower()
    forbidden = ["gated outperforms concat", "gated is superior", "gated fusion is superior", "gated statistically superior"]
    assert not any(term in text for term in forbidden)


def test_xai_source_marked_posthoc_when_ready() -> None:
    xai = pd.read_csv("figures/source_data/fig6_xai_case_source_data.csv")
    assert xai["notes"].str.contains("post-hoc", case=False, na=False).any()
