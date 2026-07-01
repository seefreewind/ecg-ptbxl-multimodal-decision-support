from __future__ import annotations

import pandas as pd


def test_structured_attribution_outputs_top_features_without_leakage_terms() -> None:
    top = pd.read_csv("tables/table_top_structured_features_global.csv")
    assert len(top) > 0
    forbidden = ("diagnostic", "statement", "snomed", "label", "target", "scp")
    lowered = top["feature"].str.lower()
    assert not lowered.apply(lambda value: any(term in value for term in forbidden)).any()
    assert {"model_name", "feature", "attribution_mean_abs", "rank"}.issubset(top.columns)


def test_structured_case_attribution_has_case_level_top_features() -> None:
    case_attr = pd.read_csv("results/xai/structured_case_attributions.csv")
    assert case_attr["rank"].max() >= 10
    assert {"ecg_id", "model_name", "label", "feature", "attribution_abs"}.issubset(case_attr.columns)
