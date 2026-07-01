from __future__ import annotations

import pandas as pd


def test_risk_coverage_retained_plus_referred_equals_total() -> None:
    metrics = pd.read_csv("results/uncertainty/risk_coverage_metrics_test.csv")
    totals = metrics["retained_n"] + metrics["referred_n"]
    assert set(totals.unique()) == {2198}


def test_risk_coverage_100_percent_retains_all() -> None:
    metrics = pd.read_csv("results/uncertainty/risk_coverage_metrics_test.csv")
    at100 = metrics[metrics["coverage"].eq(1.0)]
    assert (at100["retained_n"] == 2198).all()
    assert (at100["referred_n"] == 0).all()


def test_risk_coverage_80_percent_is_close_to_expected() -> None:
    metrics = pd.read_csv("results/uncertainty/risk_coverage_metrics_test.csv")
    at80 = metrics[metrics["coverage"].eq(0.8)]
    retained_fraction = at80["retained_n"] / (at80["retained_n"] + at80["referred_n"])
    assert ((retained_fraction > 0.75) & (retained_fraction < 0.85)).all()
