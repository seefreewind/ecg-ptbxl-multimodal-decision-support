from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score


def default_threshold_grid() -> np.ndarray:
    return np.round(np.arange(0.05, 0.951, 0.01), 2)


def apply_thresholds(y_prob: np.ndarray, thresholds: dict[str, float] | np.ndarray) -> np.ndarray:
    probs = np.asarray(y_prob)
    if isinstance(thresholds, dict):
        values = np.asarray(list(thresholds.values()), dtype=float)
    else:
        values = np.asarray(thresholds, dtype=float)
    if values.ndim != 1 or values.shape[0] != probs.shape[1]:
        raise ValueError("Threshold count must match number of prediction columns.")
    return (probs >= values.reshape(1, -1)).astype(int)


def tune_per_class_thresholds(
    y_true_val: np.ndarray,
    y_prob_val: np.ndarray,
    metric: str = "f1",
    grid: np.ndarray | None = None,
    label_names: list[str] | None = None,
) -> dict[str, float]:
    if metric != "f1":
        raise ValueError("Only F1 threshold tuning is currently supported.")
    y_true = np.asarray(y_true_val).astype(int)
    y_prob = np.asarray(y_prob_val)
    if y_true.shape != y_prob.shape:
        raise ValueError("y_true_val and y_prob_val must have the same shape.")
    grid = default_threshold_grid() if grid is None else np.asarray(grid, dtype=float)
    label_names = label_names or [f"class_{idx}" for idx in range(y_true.shape[1])]
    thresholds: dict[str, float] = {}
    for idx, label in enumerate(label_names):
        best_threshold = 0.5
        best_score = -1.0
        for threshold in grid:
            pred = (y_prob[:, idx] >= threshold).astype(int)
            score = f1_score(y_true[:, idx], pred, zero_division=0)
            if score > best_score:
                best_score = float(score)
                best_threshold = float(threshold)
        thresholds[str(label)] = best_threshold
    return thresholds


def save_thresholds(thresholds: dict[str, float], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(thresholds, indent=2, sort_keys=True), encoding="utf-8")


def load_thresholds(path: str | Path) -> dict[str, float]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(key): float(value) for key, value in data.items()}

