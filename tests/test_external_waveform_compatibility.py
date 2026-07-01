from __future__ import annotations

import pandas as pd


def test_waveform_compatibility_requires_twelve_leads_or_documented_mapping() -> None:
    compat = pd.read_csv("tables/table_external_waveform_compatibility.csv")

    incompatible = compat[~compat["compatible_with_signal_model"].astype(bool)]
    if not incompatible.empty:
        assert incompatible["blocking_issue"].replace("", pd.NA).notna().all()

    compatible = compat[compat["compatible_with_signal_model"].astype(bool)]
    if not compatible.empty:
        assert (compatible["lead_count"].astype(int) == 12).all()
        assert compatible["lead_order_detected"].str.contains("I,II,III").all()


def test_structured_features_missing_prevents_full_multimodal_external_validation() -> None:
    structured = pd.read_csv("tables/table_external_structured_feature_compatibility.csv")
    missing = structured[~structured["matches_ptbxl_plus_features"].astype(bool)]

    assert len(missing) >= 1
    assert not missing["can_run_fair_concat"].astype(bool).any()
    assert not missing["can_run_gated_fusion"].astype(bool).any()
