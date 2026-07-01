from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.calibration import arrays_from_prediction_frame, multilabel_calibration_metrics
from src.evaluation.collect_model_predictions import LABELS
from src.evaluation.evaluate_calibration import _apply_temperature_if_available


BOOTSTRAP_MODELS = ["strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"]


def bootstrap_calibration_metrics(n_bootstrap: int = 1000, seed: int = 2026) -> pd.DataFrame:
    calibration_dir = Path("results/calibration")
    manifest = pd.read_csv(calibration_dir / "prediction_manifest.csv")
    lookup = {row["model_name"]: row for row in manifest.to_dict("records")}
    rng = np.random.default_rng(seed)
    rows = []
    for model_name in BOOTSTRAP_MODELS:
        raw_predictions = pd.read_csv(lookup[model_name]["test_prediction_path"])
        prediction_modes = [
            ("raw", raw_predictions),
            ("temperature_scaled", _apply_temperature_if_available(raw_predictions, model_name, calibration_dir)),
        ]
        for calibration_mode, predictions in prediction_modes:
            y_true, y_prob = arrays_from_prediction_frame(predictions, LABELS)
            estimate = multilabel_calibration_metrics(y_true, y_prob, LABELS)
            indices = np.arange(len(predictions))
            boot_values = {"macro_brier": [], "macro_ece": []}
            for _ in range(n_bootstrap):
                sample = rng.choice(indices, size=len(indices), replace=True)
                metrics = multilabel_calibration_metrics(y_true[sample], y_prob[sample], LABELS)
                boot_values["macro_brier"].append(metrics["macro_brier"])
                boot_values["macro_ece"].append(metrics["macro_ece"])
            for metric in ["macro_brier", "macro_ece"]:
                lo, hi = np.percentile(boot_values[metric], [2.5, 97.5])
                rows.append(
                    {
                        "model_name": model_name,
                        "split": "test",
                        "calibration_mode": calibration_mode,
                        "metric": metric,
                        "estimate": estimate[metric],
                        "ci_lower": float(lo),
                        "ci_upper": float(hi),
                        "n_bootstrap": n_bootstrap,
                        "seed": seed,
                    }
                )
    out = pd.DataFrame(rows)
    calibration_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    out.to_csv(calibration_dir / "calibration_bootstrap_ci.csv", index=False)
    out.to_csv("tables/table_calibration_bootstrap_ci.csv", index=False)
    return out


def main() -> None:
    out = bootstrap_calibration_metrics()
    print(f"Wrote calibration bootstrap CI table with {len(out)} rows.")


if __name__ == "__main__":
    main()
