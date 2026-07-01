from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]


def net_benefit_binary(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> dict[str, float]:
    if threshold <= 0 or threshold >= 1:
        raise ValueError("DCA threshold must be between 0 and 1.")
    truth = np.asarray(y_true).astype(int)
    prob = np.asarray(y_prob, dtype=float)
    pred = prob >= threshold
    n = len(truth)
    tp = int(((pred == 1) & (truth == 1)).sum())
    fp = int(((pred == 1) & (truth == 0)).sum())
    tn = int(((pred == 0) & (truth == 0)).sum())
    fn = int(((pred == 0) & (truth == 1)).sum())
    prevalence = float(truth.mean()) if n else np.nan
    harm = threshold / (1.0 - threshold)
    net_benefit = float(tp / n - fp / n * harm) if n else np.nan
    treat_all = float(prevalence - (1.0 - prevalence) * harm) if n else np.nan
    return {
        "prevalence": prevalence,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "net_benefit": net_benefit,
        "treat_all_net_benefit": treat_all,
        "treat_none_net_benefit": 0.0,
        "net_benefit_vs_treat_all": net_benefit - treat_all,
        "net_benefit_vs_treat_none": net_benefit,
    }


def threshold_grid() -> pd.DataFrame:
    rows = []
    for threshold in np.round(np.arange(0.01, 0.501, 0.01), 2):
        rows.append(
            {
                "threshold": float(threshold),
                "grid_name": "0.01_to_0.50",
                "include_in_main_plot": bool(0.05 <= threshold <= 0.40),
                "notes": "Full exploratory DCA grid.",
            }
        )
    for name, lo, hi in [("0.05_to_0.40", 0.05, 0.40), ("0.10_to_0.30", 0.10, 0.30)]:
        for threshold in np.round(np.arange(lo, hi + 0.001, 0.01), 2):
            rows.append(
                {
                    "threshold": float(threshold),
                    "grid_name": name,
                    "include_in_main_plot": bool(name == "0.05_to_0.40"),
                    "notes": "Exploratory threshold range; not a clinical threshold recommendation.",
                }
            )
    return pd.DataFrame(rows)


def prediction_columns(frame: pd.DataFrame, prefix: str) -> list[str]:
    preferred = [f"{prefix}_{label}" for label in LABELS]
    if all(col in frame.columns for col in preferred):
        return preferred
    legacy = [f"{label}_{prefix}" for label in LABELS]
    if all(col in frame.columns for col in legacy):
        return legacy
    raise ValueError(f"Missing columns for prefix={prefix}")


def load_temperature_scaled_predictions(model_name: str, split: str = "test") -> pd.DataFrame:
    manifest = pd.read_csv("results/calibration/prediction_manifest.csv")
    row = manifest[manifest["model_name"].eq(model_name)].iloc[0]
    path = Path(row["test_prediction_path"] if split == "test" else row["val_prediction_path"])
    frame = pd.read_csv(path)
    logit_cols = prediction_columns(frame, "logit")
    true_cols = prediction_columns(frame, "y_true")
    logits = frame[logit_cols].to_numpy(float)
    temps = np.ones(len(LABELS), dtype=float)
    for temp_path in Path("results/calibration").glob("temperature_params_*.json"):
        payload = json.loads(temp_path.read_text())
        if payload.get("model_name") == model_name and payload.get("status") == "fitted":
            temps = np.asarray(payload["temperatures"], dtype=float)
            break
    probs = 1.0 / (1.0 + np.exp(-(logits / temps.reshape(1, -1))))
    out = frame[["ecg_id"]].copy()
    out["split"] = split
    for idx, label in enumerate(LABELS):
        out[f"y_true_{label}"] = frame[true_cols[idx]].astype(int)
        out[f"prob_{label}"] = probs[:, idx]
    return out


def dca_by_label(model_name: str, predictions: pd.DataFrame, thresholds: np.ndarray, probability_mode: str = "temperature_scaled") -> pd.DataFrame:
    rows = []
    for label in LABELS:
        y_true = predictions[f"y_true_{label}"].to_numpy(int)
        y_prob = predictions[f"prob_{label}"].to_numpy(float)
        for threshold in thresholds:
            try:
                metrics = net_benefit_binary(y_true, y_prob, float(threshold))
                reason = ""
            except Exception as exc:
                metrics = {
                    "prevalence": np.nan,
                    "tp": np.nan,
                    "fp": np.nan,
                    "tn": np.nan,
                    "fn": np.nan,
                    "net_benefit": np.nan,
                    "treat_all_net_benefit": np.nan,
                    "treat_none_net_benefit": 0.0,
                    "net_benefit_vs_treat_all": np.nan,
                    "net_benefit_vs_treat_none": np.nan,
                }
                reason = str(exc)
            rows.append(
                {
                    "model_name": model_name,
                    "probability_mode": probability_mode,
                    "split": "test",
                    "label": label,
                    "threshold": float(threshold),
                    **metrics,
                    "reason": reason,
                }
            )
    return pd.DataFrame(rows)


def macro_dca(by_label: pd.DataFrame) -> pd.DataFrame:
    grouped = by_label.groupby(["model_name", "probability_mode", "split", "threshold"], as_index=False)
    return grouped.agg(
        macro_net_benefit=("net_benefit", "mean"),
        macro_treat_all_net_benefit=("treat_all_net_benefit", "mean"),
        macro_treat_none_net_benefit=("treat_none_net_benefit", "mean"),
        macro_net_benefit_vs_treat_all=("net_benefit_vs_treat_all", "mean"),
        macro_net_benefit_vs_treat_none=("net_benefit_vs_treat_none", "mean"),
    )
