from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score


def _safe_binary_metric(fn, y_true: np.ndarray, y_score: np.ndarray) -> float:
    try:
        value = float(fn(y_true, y_score))
    except ValueError:
        return math.nan
    return value


def compute_multilabel_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    label_names: Sequence[str],
    split: str,
    threshold: float = 0.5,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    per_label_auroc: list[float] = []
    per_label_ap: list[float] = []
    per_label_f1: list[float] = []
    y_pred = (y_prob >= threshold).astype(int)

    for idx, label in enumerate(label_names):
        truth = y_true[:, idx].astype(int)
        prob = y_prob[:, idx]
        pred = y_pred[:, idx]
        auroc = _safe_binary_metric(roc_auc_score, truth, prob)
        ap = _safe_binary_metric(average_precision_score, truth, prob)
        f1 = _safe_binary_metric(lambda a, b: f1_score(a, b, zero_division=0), truth, pred)
        per_label_auroc.append(auroc)
        per_label_ap.append(ap)
        per_label_f1.append(f1)
        rows.append(
            {
                "split": split,
                "label": str(label),
                "auroc": auroc,
                "average_precision": ap,
                "f1": f1,
                "positive_count": int(truth.sum()),
            }
        )

    macro = {
        "split": split,
        "label": "macro",
        "auroc": float(np.nanmean(per_label_auroc)) if per_label_auroc else math.nan,
        "average_precision": float(np.nanmean(per_label_ap)) if per_label_ap else math.nan,
        "f1": float(np.nanmean(per_label_f1)) if per_label_f1 else math.nan,
        "positive_count": int(y_true.sum()),
    }
    return pd.DataFrame([macro] + rows, columns=["split", "label", "auroc", "average_precision", "f1", "positive_count"])

