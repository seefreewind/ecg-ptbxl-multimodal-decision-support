from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss


@dataclass(frozen=True)
class CalibrationResult:
    brier: float
    ece: float
    mce: float


def brier_binary(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    return float(brier_score_loss(np.asarray(y_true).astype(int), np.asarray(y_prob, dtype=float)))


def calibration_bins(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    truth = np.asarray(y_true).astype(int)
    prob = np.asarray(y_prob, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    for idx, (left, right) in enumerate(zip(bins[:-1], bins[1:])):
        mask = (prob >= left) & (prob < right if right < 1.0 else prob <= right)
        count = int(mask.sum())
        confidence = float(np.mean(prob[mask])) if count else float("nan")
        accuracy = float(np.mean(truth[mask])) if count else float("nan")
        rows.append(
            {
                "bin": idx,
                "bin_left": float(left),
                "bin_right": float(right),
                "confidence": confidence,
                "accuracy": accuracy,
                "count": count,
            }
        )
    return pd.DataFrame(rows)


def ece_mce_binary(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> tuple[float, float]:
    bins = calibration_bins(y_true, y_prob, n_bins=n_bins)
    total = float(bins["count"].sum())
    if total <= 0:
        return float("nan"), float("nan")
    gaps = (bins["accuracy"] - bins["confidence"]).abs()
    weights = bins["count"] / total
    ece = float((gaps.fillna(0.0) * weights).sum())
    mce = float(gaps.dropna().max()) if gaps.notna().any() else float("nan")
    return ece, mce


def calibration_binary(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> CalibrationResult:
    ece, mce = ece_mce_binary(y_true, y_prob, n_bins=n_bins)
    return CalibrationResult(brier=brier_binary(y_true, y_prob), ece=ece, mce=mce)


def multilabel_calibration_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    label_names: Sequence[str],
    n_bins: int = 10,
) -> dict[str, float]:
    truth = np.asarray(y_true).astype(int)
    prob = np.asarray(y_prob, dtype=float)
    rows: dict[str, float] = {}
    briers = []
    eces = []
    mces = []
    for idx, label in enumerate(label_names):
        result = calibration_binary(truth[:, idx], prob[:, idx], n_bins=n_bins)
        rows[f"classwise_brier_{label}"] = result.brier
        rows[f"classwise_ece_{label}"] = result.ece
        rows[f"classwise_mce_{label}"] = result.mce
        briers.append(result.brier)
        eces.append(result.ece)
        mces.append(result.mce)
    rows["macro_brier"] = float(np.nanmean(briers))
    rows["macro_ece"] = float(np.nanmean(eces))
    rows["macro_mce"] = float(np.nanmean(mces))
    return rows


def arrays_from_prediction_frame(predictions: pd.DataFrame, labels: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
    if all(f"y_true_{label}" in predictions.columns for label in labels):
        true_cols = [f"y_true_{label}" for label in labels]
    else:
        true_cols = [f"{label}_true" for label in labels]
    if all(f"prob_{label}" in predictions.columns for label in labels):
        prob_cols = [f"prob_{label}" for label in labels]
    else:
        prob_cols = [f"{label}_prob" for label in labels]
    missing = [col for col in true_cols + prob_cols if col not in predictions.columns]
    if missing:
        raise ValueError(f"Prediction file is missing required columns: {missing}")
    return predictions[true_cols].to_numpy(dtype=np.float32), predictions[prob_cols].to_numpy(dtype=np.float32)
