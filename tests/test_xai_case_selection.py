from __future__ import annotations

import pandas as pd


def test_xai_case_selection_contains_retained_referred_and_errors() -> None:
    cases = pd.read_csv("results/xai/xai_case_selection.csv")
    assert {"retained", "referred"}.issubset(set(cases["retained_or_referred"]))
    assert {"correct", "incorrect"}.issubset(set(cases["correct_or_incorrect"]))
    assert len(cases) >= 8
