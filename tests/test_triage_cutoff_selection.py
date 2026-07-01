from __future__ import annotations

import numpy as np
import pandas as pd


def test_validation_cutoffs_use_validation_frame_only() -> None:
    from src.evaluation.select_triage_cutoffs import select_validation_cutoffs

    frame = pd.DataFrame(
        {
            "model_name": ["m"] * 10,
            "probability_mode": ["raw"] * 10,
            "entropy_macro": np.linspace(0, 0.9, 10),
        }
    )
    cutoffs = select_validation_cutoffs(frame, coverage_levels=[1.0, 0.8], uncertainty_scores=["entropy_macro"])

    assert cutoffs[cutoffs["coverage"].eq(1.0)]["validation_uncertainty_cutoff"].iloc[0] == float("inf")
    at80 = cutoffs[cutoffs["coverage"].eq(0.8)].iloc[0]
    assert at80["validation_retained_n"] == 8
    assert at80["validation_referred_n"] == 2
    assert at80["cutoff_source"] == "validation"
