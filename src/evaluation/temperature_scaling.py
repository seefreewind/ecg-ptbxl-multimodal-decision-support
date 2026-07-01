from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.collect_model_predictions import LABELS


TEMPERATURE_OUTPUTS = {
    "strong_signal_only": "temperature_params_signal_strong.json",
    "signal_embedding_mlp": "temperature_params_signal_embedding_mlp.json",
    "structured_mlp": "temperature_params_structured_mlp.json",
    "fair_concat_mlp": "temperature_params_fair_concat.json",
    "gated_fusion_mlp": "temperature_params_gated_fusion.json",
}


def _binary_cross_entropy(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    prob = np.clip(y_prob, 1e-7, 1 - 1e-7)
    return float(-np.mean(y_true * np.log(prob) + (1 - y_true) * np.log(1 - prob)))


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def fit_per_class_temperatures(y_true: np.ndarray, logits: np.ndarray) -> list[float]:
    grid = np.concatenate([np.linspace(0.25, 1.0, 31), np.linspace(1.05, 5.0, 80)])
    temperatures: list[float] = []
    for idx in range(y_true.shape[1]):
        losses = []
        for temp in grid:
            losses.append(_binary_cross_entropy(y_true[:, idx], _sigmoid(logits[:, idx] / temp)))
        temperatures.append(float(grid[int(np.argmin(losses))]))
    return temperatures


def _load_arrays(frame: pd.DataFrame, suffix: str) -> tuple[np.ndarray, np.ndarray]:
    y_cols = [f"y_true_{label}" for label in LABELS] if all(f"y_true_{label}" in frame.columns for label in LABELS) else [f"{label}_true" for label in LABELS]
    if suffix == "logit" and all(f"logit_{label}" in frame.columns for label in LABELS):
        value_cols = [f"logit_{label}" for label in LABELS]
    elif suffix == "prob" and all(f"prob_{label}" in frame.columns for label in LABELS):
        value_cols = [f"prob_{label}" for label in LABELS]
    else:
        value_cols = [f"{label}_{suffix}" for label in LABELS]
    missing = [col for col in y_cols + value_cols if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns for temperature scaling: {missing}")
    return frame[y_cols].to_numpy(dtype=np.float32), frame[value_cols].to_numpy(dtype=np.float32)


def write_temperature_params(
    manifest_path: str | Path = "results/calibration/prediction_manifest.csv",
    output_dir: str | Path = "results/calibration",
) -> list[dict[str, object]]:
    manifest = pd.read_csv(manifest_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payloads = []
    for row in manifest.to_dict("records"):
        model_name = str(row["model_name"])
        if model_name not in TEMPERATURE_OUTPUTS:
            continue
        logit_available = bool(row["logit_columns_available"])
        payload: dict[str, object] = {
            "model_name": model_name,
            "temperature_type": "per_class",
            "class_names": LABELS,
            "temperatures": None,
            "fitted_on_split": "validation",
            "optimization_metric": "binary_cross_entropy",
            "status": "fitted",
            "skipped_reason": "",
        }
        if not logit_available:
            payload.update(
                {
                    "temperature_type": "skipped_logits_unavailable",
                    "temperatures": [],
                    "status": "skipped",
                    "skipped_reason": "Validation and/or test prediction files do not contain per-class logit columns.",
                }
            )
        else:
            val_frame = pd.read_csv(row["val_prediction_path"])
            y_true, logits = _load_arrays(val_frame, "logit")
            payload["temperatures"] = fit_per_class_temperatures(y_true, logits)
        out_path = out_dir / TEMPERATURE_OUTPUTS[model_name]
        out_path.write_text(json.dumps(payload, indent=2) + "\n")
        payloads.append(payload)
    return payloads


def main() -> None:
    payloads = write_temperature_params()
    fitted = sum(1 for item in payloads if item["status"] == "fitted")
    skipped = sum(1 for item in payloads if item["status"] == "skipped")
    print(f"Wrote temperature parameter files: fitted={fitted}, skipped={skipped}")


if __name__ == "__main__":
    main()
