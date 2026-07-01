from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, roc_auc_score

from src.evaluation.calibration import ece_mce_binary
from src.evaluation.uncertainty import LABELS


def _safe_metric(fn, *args) -> float:
    try:
        return float(fn(*args))
    except ValueError:
        return math.nan


def _threshold_values(thresholds: dict[str, float], labels: list[str]) -> np.ndarray:
    return np.asarray([float(thresholds[label]) for label in labels], dtype=float)


def _arrays(frame: pd.DataFrame, labels: list[str]) -> tuple[np.ndarray, np.ndarray]:
    y = frame[[f"y_true_{label}" for label in labels]].to_numpy(dtype=int)
    p = frame[[f"prob_{label}" for label in labels]].to_numpy(dtype=float)
    return y, p


def subset_metrics(frame: pd.DataFrame, thresholds: dict[str, float], labels: list[str] | None = None) -> dict[str, float]:
    labels = labels or LABELS
    if len(frame) == 0:
        return {
            "macro_auroc": math.nan,
            "macro_average_precision": math.nan,
            "macro_f1": math.nan,
            "micro_f1": math.nan,
            "brier": math.nan,
            "ece": math.nan,
        }
    y_true, y_prob = _arrays(frame, labels)
    threshold_arr = _threshold_values(thresholds, labels)
    y_pred = (y_prob >= threshold_arr.reshape(1, -1)).astype(int)
    aurocs = []
    aps = []
    f1s = []
    briers = []
    eces = []
    for idx in range(len(labels)):
        aurocs.append(_safe_metric(roc_auc_score, y_true[:, idx], y_prob[:, idx]))
        aps.append(_safe_metric(average_precision_score, y_true[:, idx], y_prob[:, idx]))
        f1s.append(_safe_metric(lambda a, b: f1_score(a, b, zero_division=0), y_true[:, idx], y_pred[:, idx]))
        briers.append(_safe_metric(brier_score_loss, y_true[:, idx], y_prob[:, idx]))
        ece, _mce = ece_mce_binary(y_true[:, idx], y_prob[:, idx], n_bins=10)
        eces.append(ece)
    return {
        "macro_auroc": float(np.nanmean(aurocs)),
        "macro_average_precision": float(np.nanmean(aps)),
        "macro_f1": float(np.nanmean(f1s)),
        "micro_f1": _safe_metric(lambda a, b: f1_score(a.ravel(), b.ravel(), zero_division=0), y_true, y_pred),
        "brier": float(np.nanmean(briers)),
        "ece": float(np.nanmean(eces)),
    }


def evaluate_risk_coverage(
    uncertainty_frames: pd.DataFrame,
    cutoffs: pd.DataFrame,
    thresholds_by_model: dict[str, dict[str, float]],
    split: str,
    labels: list[str] | None = None,
) -> pd.DataFrame:
    labels = labels or LABELS
    rows = []
    split_frame = uncertainty_frames[uncertainty_frames["split"].eq(split)]
    for cutoff in cutoffs.to_dict("records"):
        model_name = str(cutoff["model_name"])
        probability_mode = str(cutoff["probability_mode"])
        uncertainty_score = str(cutoff["uncertainty_score"])
        group = split_frame[
            split_frame["model_name"].eq(model_name)
            & split_frame["probability_mode"].eq(probability_mode)
        ]
        if group.empty:
            continue
        if split == "validation":
            mask = group[uncertainty_score].to_numpy(dtype=float) <= float(cutoff["validation_uncertainty_cutoff"])
        else:
            mask = group[uncertainty_score].to_numpy(dtype=float) <= float(cutoff["validation_uncertainty_cutoff"])
        retained = group[mask]
        referred = group[~mask]
        thresholds = thresholds_by_model[model_name]
        retained_metrics = subset_metrics(retained, thresholds, labels)
        referred_metrics = subset_metrics(referred, thresholds, labels)
        overall_metrics = subset_metrics(group, thresholds, labels)
        rows.append(
            {
                "model_name": model_name,
                "probability_mode": probability_mode,
                "uncertainty_score": uncertainty_score,
                "split": split,
                "coverage": float(cutoff["coverage"]),
                "cutoff_source": "validation",
                "uncertainty_cutoff": float(cutoff["validation_uncertainty_cutoff"]),
                "retained_n": int(len(retained)),
                "referred_n": int(len(referred)),
                "referral_fraction": float(len(referred) / len(group)),
                "retained_macro_auroc": retained_metrics["macro_auroc"],
                "retained_macro_average_precision": retained_metrics["macro_average_precision"],
                "retained_macro_f1": retained_metrics["macro_f1"],
                "retained_micro_f1": retained_metrics["micro_f1"],
                "retained_brier": retained_metrics["brier"],
                "retained_ece": retained_metrics["ece"],
                "referred_macro_auroc": referred_metrics["macro_auroc"],
                "referred_macro_f1": referred_metrics["macro_f1"],
                "overall_macro_auroc": overall_metrics["macro_auroc"],
                "overall_macro_f1": overall_metrics["macro_f1"],
                "reason": "" if len(retained) > 0 and len(referred) > 0 else "empty retained or referred subset at this coverage",
            }
        )
    return pd.DataFrame(rows)


def referred_subset_characteristics(
    uncertainty_frames: pd.DataFrame,
    metrics: pd.DataFrame,
    thresholds_by_model: dict[str, dict[str, float]],
    split: str = "test",
    labels: list[str] | None = None,
) -> pd.DataFrame:
    labels = labels or LABELS
    rows = []
    split_frame = uncertainty_frames[uncertainty_frames["split"].eq(split)]
    for row in metrics[metrics["split"].eq(split)].to_dict("records"):
        group = split_frame[
            split_frame["model_name"].eq(row["model_name"])
            & split_frame["probability_mode"].eq(row["probability_mode"])
        ]
        referred = group[group[row["uncertainty_score"]].to_numpy(dtype=float) > float(row["uncertainty_cutoff"])]
        y_true, y_prob = _arrays(referred, labels) if len(referred) else (np.empty((0, len(labels))), np.empty((0, len(labels))))
        thresholds = _threshold_values(thresholds_by_model[str(row["model_name"])], labels)
        y_pred = (y_prob >= thresholds.reshape(1, -1)).astype(int) if len(referred) else np.empty((0, len(labels)))
        payload = {
            "model_name": row["model_name"],
            "probability_mode": row["probability_mode"],
            "coverage": row["coverage"],
            "uncertainty_score": row["uncertainty_score"],
            "referred_n": int(len(referred)),
            "referral_fraction": float(row["referral_fraction"]),
            "mean_predicted_labels_per_record": float(y_pred.sum(axis=1).mean()) if len(referred) else math.nan,
            "mean_entropy": float(referred["entropy_macro"].mean()) if len(referred) else math.nan,
            "mean_margin_uncertainty": float(referred["margin_uncertainty"].mean()) if len(referred) else math.nan,
            "error_rate_if_available": float(np.any(y_pred != y_true, axis=1).mean()) if len(referred) else math.nan,
        }
        for idx, label in enumerate(labels):
            payload[f"{label}_prevalence"] = float(y_true[:, idx].mean()) if len(referred) else math.nan
        rows.append(payload)
    return pd.DataFrame(rows)
