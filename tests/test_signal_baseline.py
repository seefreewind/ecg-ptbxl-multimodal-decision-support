from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch


def test_signal_resnet_outputs_multilabel_logits() -> None:
    from src.models.signal_resnet import SignalResNet

    model = SignalResNet(in_channels=12, num_classes=5, base_channels=8, blocks_per_stage=(1, 1, 1))
    x = torch.randn(2, 12, 1000)

    logits = model(x)

    assert tuple(logits.shape) == (2, 5)


def test_compute_multilabel_metrics_returns_stable_schema() -> None:
    from src.training.metrics import compute_multilabel_metrics

    y_true = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.float32)
    y_prob = np.array([[0.9, 0.2], [0.1, 0.8], [0.7, 0.6]], dtype=np.float32)

    metrics = compute_multilabel_metrics(y_true, y_prob, label_names=["A", "B"], split="test")

    assert list(metrics.columns) == ["split", "label", "auroc", "average_precision", "f1", "positive_count"]
    assert set(metrics["label"]) == {"macro", "A", "B"}
    assert metrics.loc[metrics["label"].eq("A"), "positive_count"].item() == 2


def test_training_dry_run_writes_expected_outputs(tmp_path: Path) -> None:
    from src.training.train_signal import train

    output_dir = tmp_path / "results" / "internal"
    table_dir = tmp_path / "tables"
    model_dir = tmp_path / "models"
    config_path = tmp_path / "signal.yaml"
    config_path.write_text(
        f"""
data:
  train_csv: data/splits/ptbxl_train.csv
  val_csv: data/splits/ptbxl_val.csv
  test_csv: data/splits/ptbxl_test.csv
  records_base_dir: data/raw/ptbxl
  labels: [NORM, MI, STTC, CD, HYP]
training:
  dry_run: true
  max_train_batches: 1
  max_eval_batches: 1
  batch_size: 2
  num_workers: 0
model:
  base_channels: 4
  blocks_per_stage: [1, 1]
output:
  metrics_csv: {output_dir / "signal_baseline_metrics.csv"}
  table_csv: {table_dir / "table_signal_baseline_results.csv"}
  val_predictions_csv: {output_dir / "signal_val_predictions.csv"}
  test_predictions_csv: {output_dir / "signal_test_predictions.csv"}
  history_csv: {output_dir / "signal_training_history.csv"}
  run_summary_json: {output_dir / "signal_run_summary.json"}
  checkpoint_path: {model_dir / "signal_resnet.pt"}
""",
        encoding="utf-8",
    )

    status = train(config_path)

    metrics_path = output_dir / "signal_baseline_metrics.csv"
    table_path = table_dir / "table_signal_baseline_results.csv"
    val_predictions_path = output_dir / "signal_val_predictions.csv"
    test_predictions_path = output_dir / "signal_test_predictions.csv"
    history_path = output_dir / "signal_training_history.csv"
    summary_path = output_dir / "signal_run_summary.json"
    checkpoint_path = model_dir / "signal_resnet.pt"
    assert status == 0
    assert metrics_path.exists() and metrics_path.stat().st_size > 0
    assert table_path.exists() and table_path.stat().st_size > 0
    assert val_predictions_path.exists() and val_predictions_path.stat().st_size > 0
    assert test_predictions_path.exists() and test_predictions_path.stat().st_size > 0
    assert history_path.exists() and history_path.stat().st_size > 0
    assert summary_path.exists() and summary_path.stat().st_size > 0
    assert checkpoint_path.exists() and checkpoint_path.stat().st_size > 0
    metrics = pd.read_csv(metrics_path)
    assert {"split", "label", "auroc", "average_precision", "f1", "positive_count"}.issubset(metrics.columns)
    predictions = pd.read_csv(test_predictions_path)
    assert {"ecg_id", "NORM_true", "NORM_prob", "HYP_true", "HYP_prob"}.issubset(predictions.columns)


def test_repeated_seed_summary_aggregates_macro_metrics() -> None:
    from src.training.run_signal_repeated import summarise_repeated_seed_metrics

    metrics = pd.DataFrame(
        [
            {"seed": 1, "split": "test", "label": "macro", "auroc": 0.8, "average_precision": 0.6, "f1": 0.5},
            {"seed": 2, "split": "test", "label": "macro", "auroc": 0.9, "average_precision": 0.7, "f1": 0.6},
            {"seed": 1, "split": "val", "label": "macro", "auroc": 0.7, "average_precision": 0.5, "f1": 0.4},
            {"seed": 2, "split": "val", "label": "macro", "auroc": 0.8, "average_precision": 0.6, "f1": 0.5},
        ]
    )

    summary = summarise_repeated_seed_metrics(metrics)

    assert list(summary.columns) == [
        "split",
        "label",
        "n_seeds",
        "auroc_mean",
        "auroc_std",
        "average_precision_mean",
        "average_precision_std",
        "f1_mean",
        "f1_std",
    ]
    test_row = summary[summary["split"].eq("test")].iloc[0]
    assert test_row["n_seeds"] == 2
    assert round(test_row["auroc_mean"], 3) == 0.85


def test_bootstrap_ci_uses_prediction_columns() -> None:
    from src.training.bootstrap_signal_metrics import bootstrap_macro_ci

    predictions = pd.DataFrame(
        {
            "ecg_id": [1, 2, 3, 4],
            "A_true": [1, 0, 1, 0],
            "A_prob": [0.9, 0.2, 0.8, 0.1],
            "B_true": [0, 1, 0, 1],
            "B_prob": [0.1, 0.8, 0.2, 0.9],
        }
    )

    ci = bootstrap_macro_ci(predictions, labels=["A", "B"], split="test", n_bootstrap=10, seed=1)

    assert list(ci.columns) == ["split", "metric", "estimate", "ci_lower", "ci_upper", "n_bootstrap"]
    assert set(ci["metric"]) == {"auroc", "average_precision", "f1"}
    assert ci["n_bootstrap"].eq(10).all()
