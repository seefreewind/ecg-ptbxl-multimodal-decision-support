from __future__ import annotations

from pathlib import Path

import pandas as pd


ALLOWED_MODES = {
    "signal_only_main",
    "multimodal_full",
    "multimodal_missing_modality",
    "external_feature_extraction_required",
    "not_ready",
}


def test_external_validation_mode_decision_follows_readiness_rules() -> None:
    modes = pd.read_csv("tables/table_external_validation_mode_decision.csv")

    assert set(modes["recommended_external_validation_mode"]).issubset(ALLOWED_MODES)
    not_ready = modes[modes["recommended_external_validation_mode"].eq("not_ready")]
    assert not_ready["blocking_issue"].replace("", pd.NA).notna().all()

    multimodal = modes[modes["recommended_external_validation_mode"].eq("multimodal_full")]
    if not multimodal.empty:
        assert multimodal["structured_features_compatible"].astype(bool).all()


def test_figure9_source_data_manifest_is_updated() -> None:
    manifest = pd.read_csv("figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv")
    figure9 = manifest[manifest["figure"].eq("Figure 9")]

    assert {
        "figures/source_data/fig9_external_validation_readiness.csv",
        "figures/source_data/fig9_external_label_mapping.csv",
    }.issubset(set(figure9["source_file"]))
    assert set(figure9["status"]) == {"ready"}
    assert Path("figures/source_data/fig9_external_validation_readiness.csv").exists()
    assert Path("figures/source_data/fig9_external_label_mapping.csv").exists()
