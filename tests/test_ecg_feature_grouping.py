from __future__ import annotations


def test_ecg_feature_grouping_returns_valid_groups() -> None:
    from src.figures.ecg_feature_grouping import VALID_GROUPS, group_ecg_feature

    for feature in ["R_Amp_V6", "QRS_Dur_V1", "QT_Int_V5", "P_Morph_V2_iqr", "unknown_feature"]:
        assert group_ecg_feature(feature) in VALID_GROUPS
