from __future__ import annotations

import numpy as np


def test_net_benefit_formula_and_references() -> None:
    from src.evaluation.dca import net_benefit_binary

    y_true = np.array([1, 1, 0, 0])
    y_prob = np.array([0.9, 0.8, 0.7, 0.1])
    out = net_benefit_binary(y_true, y_prob, 0.5)

    assert out["tp"] == 2
    assert out["fp"] == 1
    assert out["tn"] == 1
    assert out["fn"] == 0
    assert out["treat_none_net_benefit"] == 0.0
    assert out["net_benefit"] == 0.25
    assert out["treat_all_net_benefit"] == 0.0


def test_threshold_grid_between_zero_and_one() -> None:
    from src.evaluation.dca import threshold_grid

    grid = threshold_grid()
    assert grid["threshold"].between(0, 1, inclusive="neither").all()
    assert {"0.01_to_0.50", "0.05_to_0.40", "0.10_to_0.30"}.issubset(set(grid["grid_name"]))
