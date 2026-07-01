from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def test_concat_fusion_uses_precomputed_signal_features(tmp_path: Path) -> None:
    from src.training.train_concat_fusion import train

    labels = ["NORM", "MI", "STTC", "CD", "HYP"]
    splits = ["train"] * 8 + ["val"] * 4 + ["test"] * 4
    index_rows = []
    structured_rows = []
    signal_frames = {"train": [], "val": [], "test": []}
    for ecg_id, split in enumerate(splits, start=1):
        index_row = {"ecg_id": ecg_id, "split": split, "filename_lr": f"dummy/{ecg_id}"}
        for idx, label in enumerate(labels):
            index_row[label] = int((ecg_id + idx) % 2 == 0)
        index_rows.append(index_row)
        structured_rows.append({"ecg_id": ecg_id, "qrs_duration": float(ecg_id), "qt_interval": float(ecg_id % 5)})
        signal_row = {"ecg_id": ecg_id, "split": split}
        for idx, label in enumerate(labels):
            signal_row[f"signal_{label}_prob"] = 0.2 + 0.1 * ((ecg_id + idx) % 5)
        signal_frames[split].append(signal_row)

    index_csv = tmp_path / "index.csv"
    features_csv = tmp_path / "features.csv"
    feature_names_txt = tmp_path / "feature_names.txt"
    pd.DataFrame(index_rows).to_csv(index_csv, index=False)
    pd.DataFrame(structured_rows).to_csv(features_csv, index=False)
    feature_names_txt.write_text("qrs_duration\nqt_interval\n", encoding="utf-8")
    signal_paths = {}
    for split, rows in signal_frames.items():
        path = tmp_path / f"signal_{split}.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        signal_paths[split] = path

    output_dir = tmp_path / "results"
    table_dir = tmp_path / "tables"
    config_path = tmp_path / "concat.yaml"
    config_path.write_text(
        f"""
data:
  features_csv: {features_csv}
  index_csv: {index_csv}
  feature_names_txt: {feature_names_txt}
  signal_feature_csvs:
    train: {signal_paths['train']}
    val: {signal_paths['val']}
    test: {signal_paths['test']}
  labels: [NORM, MI, STTC, CD, HYP]
model:
  max_iter: 100
training:
  seed: 1
output:
  metrics_csv: {output_dir / "concat_fusion_metrics.csv"}
  table_csv: {table_dir / "table_concat_fusion_results.csv"}
  val_predictions_csv: {output_dir / "concat_fusion_val_predictions.csv"}
  test_predictions_csv: {output_dir / "concat_fusion_test_predictions.csv"}
  run_summary_json: {output_dir / "concat_fusion_run_summary.json"}
  model_path: {output_dir / "concat_fusion_logistic.pkl"}
""",
        encoding="utf-8",
    )

    status = train(config_path)

    assert status == 0
    metrics = pd.read_csv(output_dir / "concat_fusion_metrics.csv")
    table = pd.read_csv(table_dir / "table_concat_fusion_results.csv")
    predictions = pd.read_csv(output_dir / "concat_fusion_test_predictions.csv")
    assert set(metrics["label"]) == {"macro", *labels}
    assert table["label"].eq("macro").all()
    assert {"ecg_id", "NORM_true", "NORM_prob", "HYP_true", "HYP_prob"}.issubset(predictions.columns)
    assert (output_dir / "concat_fusion_logistic.pkl").exists()
