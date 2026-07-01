from __future__ import annotations

import math

import numpy as np
import pandas as pd


COVERAGE_LEVELS = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
UNCERTAINTY_SCORES = ["entropy_macro", "entropy_max", "margin_uncertainty"]


def select_validation_cutoffs(
    uncertainty_frame: pd.DataFrame,
    coverage_levels: list[float] | None = None,
    uncertainty_scores: list[str] | None = None,
) -> pd.DataFrame:
    coverage_levels = coverage_levels or COVERAGE_LEVELS
    uncertainty_scores = uncertainty_scores or UNCERTAINTY_SCORES
    rows = []
    grouped = uncertainty_frame.groupby(["model_name", "probability_mode"], sort=False)
    for (model_name, probability_mode), group in grouped:
        n = len(group)
        for score in uncertainty_scores:
            ordered = group.sort_values(score, ascending=True).reset_index(drop=True)
            values = ordered[score].to_numpy(dtype=float)
            for coverage in coverage_levels:
                retained_n = n if coverage >= 1.0 else max(1, int(math.ceil(n * coverage)))
                cutoff = float("inf") if coverage >= 1.0 else float(values[retained_n - 1])
                rows.append(
                    {
                        "model_name": model_name,
                        "probability_mode": probability_mode,
                        "uncertainty_score": score,
                        "coverage": coverage,
                        "validation_uncertainty_cutoff": cutoff,
                        "validation_retained_n": retained_n,
                        "validation_referred_n": n - retained_n,
                        "cutoff_source": "validation",
                        "uncertainty_direction": "larger_is_more_uncertain",
                    }
                )
    return pd.DataFrame(rows)


def apply_cutoff(frame: pd.DataFrame, uncertainty_score: str, cutoff: float) -> np.ndarray:
    return frame[uncertainty_score].to_numpy(dtype=float) <= float(cutoff)
