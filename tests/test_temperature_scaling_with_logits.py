from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def test_manifest_marks_main_models_temperature_eligible() -> None:
    manifest = pd.read_csv("results/calibration/prediction_manifest.csv")
    main = manifest[manifest["include_in_main_calibration"].astype(bool)]
    assert len(main) == 5
    assert main["logit_columns_available"].all()
    assert main["probability_columns_available"].all()
    assert main["temperature_scaling_eligible"].all()


def test_temperature_params_are_validation_only() -> None:
    paths = sorted(Path("results/calibration").glob("temperature_params_*.json"))
    assert len(paths) == 5
    for path in paths:
        payload = json.loads(path.read_text())
        assert payload["fitted_on_split"] == "validation"
        assert payload["optimization_metric"] == "binary_cross_entropy"
        assert payload["status"] == "fitted"
        assert payload["temperature_type"] == "per_class"
        assert len(payload["temperatures"]) == 5
