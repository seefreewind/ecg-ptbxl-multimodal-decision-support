from __future__ import annotations

import pandas as pd


def test_gate_weights_are_in_reasonable_range() -> None:
    gates = pd.read_csv("results/xai/gated_gate_weights_test.csv")
    assert gates["gate_signal_mean"].between(0, 1).all()
    assert gates["gate_structured_mean"].between(0, 1).all()
    assert {"retained", "referred"}.issubset(set(gates["retained_or_referred_80"]))


def test_gate_weight_summary_outputs_groups() -> None:
    summary = pd.read_csv("tables/table_gate_weight_summary.csv")
    assert {"retained", "referred"}.issubset(set(summary["retained_or_referred_80"]))
    assert {"gate_signal_mean", "gate_structured_mean"}.issubset(summary.columns)
