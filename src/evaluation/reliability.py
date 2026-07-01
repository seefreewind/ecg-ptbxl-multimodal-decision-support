from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from src.evaluation.calibration import arrays_from_prediction_frame, calibration_bins


def reliability_curve_source(
    predictions: pd.DataFrame,
    labels: Sequence[str],
    model_name: str,
    split: str,
    calibration_mode: str,
    n_bins: int = 10,
) -> pd.DataFrame:
    y_true, y_prob = arrays_from_prediction_frame(predictions, labels)
    frames = []
    for idx, label in enumerate(labels):
        bins = calibration_bins(y_true[:, idx], y_prob[:, idx], n_bins=n_bins)
        bins.insert(0, "label", label)
        frames.append(bins)
    out = pd.concat(frames, ignore_index=True)
    out.insert(0, "calibration_mode", calibration_mode)
    out.insert(0, "split", split)
    out.insert(0, "model_name", model_name)
    return out


def confidence_histogram_source(
    predictions: pd.DataFrame,
    labels: Sequence[str],
    model_name: str,
    split: str,
    calibration_mode: str,
    n_bins: int = 10,
) -> pd.DataFrame:
    _y_true, y_prob = arrays_from_prediction_frame(predictions, labels)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    for idx, label in enumerate(labels):
        counts, edges = np.histogram(y_prob[:, idx], bins=bins)
        for bin_idx, count in enumerate(counts):
            rows.append(
                {
                    "model_name": model_name,
                    "split": split,
                    "calibration_mode": calibration_mode,
                    "label": label,
                    "bin": bin_idx,
                    "bin_left": float(edges[bin_idx]),
                    "bin_right": float(edges[bin_idx + 1]),
                    "count": int(count),
                }
            )
    return pd.DataFrame(rows)
