from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
)

from src.training.thresholds import apply_thresholds


def _safe_metric(fn, *args) -> float:
    try:
        return float(fn(*args))
    except ValueError:
        return math.nan


def _ece_binary(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for left, right in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= left) & (y_prob < right if right < 1.0 else y_prob <= right)
        if not np.any(mask):
            continue
        confidence = float(np.mean(y_prob[mask]))
        accuracy = float(np.mean(y_true[mask]))
        ece += float(np.mean(mask)) * abs(accuracy - confidence)
    return ece


def _specificity(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    try:
        tn, fp, _fn, _tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    except ValueError:
        return math.nan
    denom = tn + fp
    return float(tn / denom) if denom else math.nan


def evaluate_multilabel_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: dict[str, float] | np.ndarray | None = None,
    label_names: Sequence[str] | None = None,
    bootstrap_resamples: int = 0,
    split_name: str | None = None,
    model_name: str | None = None,
) -> pd.DataFrame:
    del bootstrap_resamples
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)
    if y_true.shape != y_prob.shape:
        raise ValueError("y_true and y_prob must have the same shape.")
    label_names = list(label_names or [f"class_{idx}" for idx in range(y_true.shape[1])])
    if thresholds is None:
        threshold_values = np.full(y_true.shape[1], 0.5, dtype=float)
    elif isinstance(thresholds, dict):
        threshold_values = np.asarray([float(thresholds[label]) for label in label_names], dtype=float)
    else:
        threshold_values = np.asarray(thresholds, dtype=float)
    y_pred = apply_thresholds(y_prob, threshold_values)

    rows: list[dict[str, Any]] = []
    per_class = {
        "auroc": [],
        "average_precision": [],
        "f1": [],
        "sensitivity": [],
        "specificity": [],
        "balanced_accuracy": [],
        "brier_score": [],
        "ece": [],
    }
    for idx, label in enumerate(label_names):
        truth = y_true[:, idx]
        prob = y_prob[:, idx]
        pred = y_pred[:, idx]
        row = {
            "model": model_name or "",
            "split": split_name or "",
            "label": str(label),
            "threshold": float(threshold_values[idx]),
            "auroc": _safe_metric(roc_auc_score, truth, prob),
            "average_precision": _safe_metric(average_precision_score, truth, prob),
            "f1": _safe_metric(lambda a, b: f1_score(a, b, zero_division=0), truth, pred),
            "sensitivity": _safe_metric(lambda a, b: recall_score(a, b, zero_division=0), truth, pred),
            "specificity": _specificity(truth, pred),
            "balanced_accuracy": _safe_metric(balanced_accuracy_score, truth, pred),
            "brier_score": _safe_metric(brier_score_loss, truth, prob),
            "ece": _ece_binary(truth, prob),
            "positive_count": int(truth.sum()),
        }
        rows.append(row)
        for metric in per_class:
            per_class[metric].append(float(row[metric]))

    micro_f1 = _safe_metric(lambda a, b: f1_score(a.ravel(), b.ravel(), zero_division=0), y_true, y_pred)
    macro = {
        "model": model_name or "",
        "split": split_name or "",
        "label": "macro",
        "threshold": math.nan,
        "auroc": float(np.nanmean(per_class["auroc"])),
        "average_precision": float(np.nanmean(per_class["average_precision"])),
        "f1": float(np.nanmean(per_class["f1"])),
        "micro_f1": micro_f1,
        "sensitivity": float(np.nanmean(per_class["sensitivity"])),
        "specificity": float(np.nanmean(per_class["specificity"])),
        "balanced_accuracy": float(np.nanmean(per_class["balanced_accuracy"])),
        "brier_score": float(np.nanmean(per_class["brier_score"])),
        "ece": float(np.nanmean(per_class["ece"])),
        "positive_count": int(y_true.sum()),
    }
    df = pd.DataFrame([macro] + rows)
    if "micro_f1" not in df.columns:
        df["micro_f1"] = math.nan
    return df[
        [
            "model",
            "split",
            "label",
            "threshold",
            "auroc",
            "average_precision",
            "f1",
            "micro_f1",
            "sensitivity",
            "specificity",
            "balanced_accuracy",
            "brier_score",
            "ece",
            "positive_count",
        ]
    ]

