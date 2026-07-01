from __future__ import annotations

import pandas as pd


def test_raw_and_scaled_calibration_tables_have_stable_schema() -> None:
    raw = pd.read_csv("tables/table_calibration_raw.csv")
    scaled = pd.read_csv("tables/table_calibration_temperature_scaled.csv")
    required = {
        "model_name",
        "split",
        "calibration_mode",
        "temperature_status",
        "n_bins",
        "macro_brier",
        "macro_ece",
        "macro_mce",
    }
    assert required.issubset(raw.columns)
    assert required.issubset(scaled.columns)
    assert set(raw["calibration_mode"]) == {"raw"}
    assert set(scaled["calibration_mode"]) == {"temperature_scaled"}


def test_temperature_scaled_delta_contains_test_improvements() -> None:
    delta = pd.read_csv("tables/table_calibration_delta.csv")
    test = delta[delta["split"].eq("test")]
    fair = test[test["model_name"].eq("fair_concat_mlp")].iloc[0]
    gated = test[test["model_name"].eq("gated_fusion_mlp")].iloc[0]
    assert fair["macro_ece"] < 0
    assert gated["macro_ece"] < 0


def test_bootstrap_ci_contains_raw_and_scaled_modes() -> None:
    ci = pd.read_csv("tables/table_calibration_bootstrap_ci.csv")
    assert {"raw", "temperature_scaled"}.issubset(set(ci["calibration_mode"]))
    assert {"macro_brier", "macro_ece"}.issubset(set(ci["metric"]))
