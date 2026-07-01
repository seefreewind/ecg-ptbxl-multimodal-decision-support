from __future__ import annotations

import json

import numpy as np


def test_temperature_grid_fits_per_class_values() -> None:
    from src.evaluation.temperature_scaling import fit_per_class_temperatures

    y_true = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.float32)
    logits = np.array([[3.0, -2.0], [-2.0, 3.0], [2.0, 1.5]], dtype=np.float32)
    temperatures = fit_per_class_temperatures(y_true, logits)

    assert len(temperatures) == 2
    assert all(temp > 0 for temp in temperatures)


def test_temperature_scaling_skips_when_logits_missing(tmp_path) -> None:
    from src.evaluation.temperature_scaling import write_temperature_params

    manifest = tmp_path / "prediction_manifest.csv"
    manifest.write_text(
        "model_name,logit_columns_available,val_prediction_path\n"
        "strong_signal_only,False,missing.csv\n"
    )
    out_dir = tmp_path / "calibration"
    payloads = write_temperature_params(manifest, out_dir)

    assert payloads[0]["status"] == "skipped"
    written = json.loads((out_dir / "temperature_params_signal_strong.json").read_text())
    assert written["temperature_type"] == "skipped_logits_unavailable"
