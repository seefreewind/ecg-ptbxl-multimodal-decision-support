from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.training.metrics import compute_multilabel_metrics
from src.utils.io import safe_to_csv


def _arrays_from_predictions(predictions: pd.DataFrame, labels: list[str]) -> tuple[np.ndarray, np.ndarray]:
    true_cols = [f"{label}_true" for label in labels]
    prob_cols = [f"{label}_prob" for label in labels]
    missing = [col for col in true_cols + prob_cols if col not in predictions.columns]
    if missing:
        raise ValueError(f"Prediction file is missing required columns: {missing}")
    return predictions[true_cols].to_numpy(dtype=np.float32), predictions[prob_cols].to_numpy(dtype=np.float32)


def bootstrap_macro_ci(
    predictions: pd.DataFrame,
    labels: list[str],
    split: str,
    n_bootstrap: int = 500,
    seed: int = 2026,
) -> pd.DataFrame:
    y_true, y_prob = _arrays_from_predictions(predictions, labels)
    rng = np.random.default_rng(seed)
    estimates = compute_multilabel_metrics(y_true, y_prob, labels, split=split)
    macro = estimates[estimates["label"].eq("macro")].iloc[0]
    boot_rows: list[dict[str, float]] = []
    n = len(predictions)
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        sample_metrics = compute_multilabel_metrics(y_true[idx], y_prob[idx], labels, split=split)
        row = sample_metrics[sample_metrics["label"].eq("macro")].iloc[0]
        boot_rows.append(
            {
                "auroc": float(row["auroc"]),
                "average_precision": float(row["average_precision"]),
                "f1": float(row["f1"]),
            }
        )
    boot = pd.DataFrame(boot_rows)
    rows = []
    for metric in ["auroc", "average_precision", "f1"]:
        rows.append(
            {
                "split": split,
                "metric": metric,
                "estimate": float(macro[metric]),
                "ci_lower": float(np.nanpercentile(boot[metric], 2.5)),
                "ci_upper": float(np.nanpercentile(boot[metric], 97.5)),
                "n_bootstrap": int(n_bootstrap),
            }
        )
    return pd.DataFrame(rows, columns=["split", "metric", "estimate", "ci_lower", "ci_upper", "n_bootstrap"])


def run(
    val_predictions: str | Path,
    test_predictions: str | Path,
    output_csv: str | Path,
    table_csv: str | Path,
    labels: list[str],
    n_bootstrap: int,
    seed: int,
) -> int:
    val = pd.read_csv(val_predictions)
    test = pd.read_csv(test_predictions)
    ci = pd.concat(
        [
            bootstrap_macro_ci(val, labels, "val", n_bootstrap=n_bootstrap, seed=seed),
            bootstrap_macro_ci(test, labels, "test", n_bootstrap=n_bootstrap, seed=seed + 1),
        ],
        ignore_index=True,
    )
    safe_to_csv(ci, output_csv)
    safe_to_csv(ci, table_csv)
    print(f"Bootstrap CI: {output_csv}")
    print(f"Bootstrap CI table: {table_csv}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap macro CIs from signal baseline predictions.")
    parser.add_argument("--val-predictions", default="results/internal/signal_val_predictions.csv")
    parser.add_argument("--test-predictions", default="results/internal/signal_test_predictions.csv")
    parser.add_argument("--output-csv", default="results/internal/signal_bootstrap_ci.csv")
    parser.add_argument("--table-csv", default="tables/table_signal_bootstrap_ci.csv")
    parser.add_argument("--labels", default="NORM,MI,STTC,CD,HYP")
    parser.add_argument("--n-bootstrap", type=int, default=500)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    labels = [label.strip() for label in args.labels.split(",") if label.strip()]
    raise SystemExit(
        run(
            args.val_predictions,
            args.test_predictions,
            args.output_csv,
            args.table_csv,
            labels,
            args.n_bootstrap,
            args.seed,
        )
    )


if __name__ == "__main__":
    main()

