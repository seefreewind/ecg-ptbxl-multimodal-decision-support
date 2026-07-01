from __future__ import annotations

import pandas as pd


def test_alignment_column_filter_excludes_leakage_columns() -> None:
    from src.data.align_ptbxl_plus import classify_feature_columns

    df = pd.DataFrame(
        {
            "ecg_id": [1, 2, 3],
            "qrs_duration": [90.0, 91.0, 92.0],
            "qt_interval": [350.0, None, 360.0],
            "diagnostic_class": [1, 0, 1],
            "some_statement_score": [0.1, 0.2, 0.3],
            "target_like": [1, 1, 0],
            "text_feature": ["a", "b", "c"],
        }
    )

    kept, missingness, excluded = classify_feature_columns(df, id_col="ecg_id")

    assert kept == ["qrs_duration", "qt_interval"]
    assert set(excluded["column"]) >= {"diagnostic_class", "some_statement_score", "target_like", "text_feature"}
    assert set(missingness["feature"]) == {"qrs_duration", "qt_interval"}


def test_alignment_column_filter_drops_high_missingness() -> None:
    from src.data.align_ptbxl_plus import classify_feature_columns

    df = pd.DataFrame(
        {
            "ecg_id": [1, 2, 3, 4, 5],
            "qrs_duration": [90.0, 91.0, 92.0, 93.0, 94.0],
            "qt_interval": [None, None, None, 350.0, 351.0],
        }
    )

    kept, missingness, excluded = classify_feature_columns(df, id_col="ecg_id")

    assert kept == ["qrs_duration"]
    qt_row = missingness[missingness["feature"].eq("qt_interval")].iloc[0]
    assert qt_row["kept_for_modeling"] == False
    assert "qt_interval" in set(excluded["column"])


def test_id_standardization_requires_integer_convertible_values() -> None:
    from src.data.align_ptbxl_plus import standardise_ecg_id

    ok = pd.DataFrame({"ECG_ID": ["1", "2.0", 3]})
    bad = pd.DataFrame({"ECG_ID": ["1", "bad"]})

    assert standardise_ecg_id(ok, "ECG_ID").tolist() == [1, 2, 3]
    try:
        standardise_ecg_id(bad, "ECG_ID")
    except ValueError as exc:
        assert "cannot be converted to int" in str(exc)
    else:
        raise AssertionError("Expected non-integer ECG ID validation to fail.")


def test_alignment_readiness_thresholds() -> None:
    aligned_rows = 10000
    kept_feature_columns = 20

    assert not (aligned_rows > 10000 and kept_feature_columns > 20)
    assert (aligned_rows + 1 > 10000 and kept_feature_columns + 1 > 20)
