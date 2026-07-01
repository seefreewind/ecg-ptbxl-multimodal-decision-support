from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]


def binary_entropy(prob: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(prob, dtype=float), 1e-7, 1.0 - 1e-7)
    return -(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))


def load_thresholds(path: str | Path, labels: list[str] | None = None) -> np.ndarray:
    labels = labels or LABELS
    data = json.loads(Path(path).read_text())
    return np.asarray([float(data[label]) for label in labels], dtype=float)


def prediction_columns(frame: pd.DataFrame, prefix: str, labels: list[str] | None = None) -> list[str]:
    labels = labels or LABELS
    preferred = [f"{prefix}_{label}" for label in labels]
    if all(col in frame.columns for col in preferred):
        return preferred
    legacy = [f"{label}_{prefix}" for label in labels]
    if all(col in frame.columns for col in legacy):
        return legacy
    raise ValueError(f"Missing {prefix} columns for labels: {labels}")


def scaled_probabilities_from_logits(frame: pd.DataFrame, model_name: str, temperature_dir: str | Path = "results/calibration") -> np.ndarray:
    logit_cols = prediction_columns(frame, "logit")
    logits = frame[logit_cols].to_numpy(dtype=float)
    for path in Path(temperature_dir).glob("temperature_params_*.json"):
        payload = json.loads(path.read_text())
        if payload.get("model_name") == model_name and payload.get("status") == "fitted":
            temps = np.asarray(payload["temperatures"], dtype=float)
            return 1.0 / (1.0 + np.exp(-(logits / temps.reshape(1, -1))))
    return 1.0 / (1.0 + np.exp(-logits))


def probabilities(frame: pd.DataFrame, model_name: str, probability_mode: str) -> np.ndarray:
    if probability_mode == "raw":
        return frame[prediction_columns(frame, "prob")].to_numpy(dtype=float)
    if probability_mode == "temperature_scaled":
        return scaled_probabilities_from_logits(frame, model_name)
    raise ValueError(f"Unsupported probability_mode: {probability_mode}")


def true_labels(frame: pd.DataFrame) -> np.ndarray:
    return frame[prediction_columns(frame, "y_true")].to_numpy(dtype=int)


def compute_uncertainty_scores(prob: np.ndarray, thresholds: np.ndarray, labels: list[str] | None = None) -> pd.DataFrame:
    labels = labels or LABELS
    entropy = binary_entropy(prob)
    margin_certainty = np.min(np.abs(prob - thresholds.reshape(1, -1)), axis=1)
    out = pd.DataFrame(
        {
            "entropy_macro": entropy.mean(axis=1),
            "entropy_max": entropy.max(axis=1),
            "margin_uncertainty": -margin_certainty,
            "margin_certainty": margin_certainty,
        }
    )
    for idx, label in enumerate(labels):
        out[f"entropy_{label}"] = entropy[:, idx]
    for score in ["entropy_macro", "entropy_max", "margin_uncertainty"]:
        values = out[score].to_numpy(dtype=float)
        min_v = float(np.nanmin(values))
        max_v = float(np.nanmax(values))
        if max_v > min_v:
            normalized_uncertainty = (values - min_v) / (max_v - min_v)
        else:
            normalized_uncertainty = np.zeros_like(values)
        out[f"confidence_from_{score}"] = 1.0 - normalized_uncertainty
    return out


def prediction_with_uncertainty(
    frame: pd.DataFrame,
    model_name: str,
    probability_mode: str,
    threshold_path: str | Path,
    labels: list[str] | None = None,
) -> pd.DataFrame:
    labels = labels or LABELS
    prob = probabilities(frame, model_name, probability_mode)
    thresholds = load_thresholds(threshold_path, labels)
    scores = compute_uncertainty_scores(prob, thresholds, labels)
    out = frame[["ecg_id", "split"]].copy()
    y_true = true_labels(frame)
    for idx, label in enumerate(labels):
        out[f"y_true_{label}"] = y_true[:, idx]
        out[f"prob_{label}"] = prob[:, idx]
    out["model_name"] = model_name
    out["probability_mode"] = probability_mode
    return pd.concat([out, scores], axis=1)
