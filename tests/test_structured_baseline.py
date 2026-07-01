from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def test_structured_baseline_writes_expected_outputs(tmp_path: Path) -> None:
    from src.training.train_structured import train

    labels = ["NORM", "MI", "STTC", "CD", "HYP"]
    rows = []
    features = []
    splits = ["train"] * 8 + ["val"] * 4 + ["test"] * 4
    for ecg_id, split in enumerate(splits, start=1):
        row = {"ecg_id": ecg_id, "split": split}
        for idx, label in enumerate(labels):
            row[label] = int((ecg_id + idx) % 2 == 0)
        rows.append(row)
        features.append(
            {
                "ecg_id": ecg_id,
                "qrs_duration": float(ecg_id),
                "qt_interval": float(ecg_id % 5),
                "rr_mean": np.nan if ecg_id == 3 else float(ecg_id + 1),
            }
        )

    index_csv = tmp_path / "index.csv"
    features_csv = tmp_path / "features.csv"
    feature_names_txt = tmp_path / "feature_names.txt"
    pd.DataFrame(rows).to_csv(index_csv, index=False)
    pd.DataFrame(features).to_csv(features_csv, index=False)
    feature_names_txt.write_text("qrs_duration\nqt_interval\nrr_mean\n", encoding="utf-8")

    output_dir = tmp_path / "results"
    table_dir = tmp_path / "tables"
    config_path = tmp_path / "structured.yaml"
    config_path.write_text(
        f"""
data:
  features_csv: {features_csv}
  index_csv: {index_csv}
  feature_names_txt: {feature_names_txt}
  labels: [NORM, MI, STTC, CD, HYP]
model:
  max_iter: 100
training:
  seed: 1
output:
  metrics_csv: {output_dir / "structured_baseline_metrics.csv"}
  table_csv: {table_dir / "table_structured_baseline_results.csv"}
  val_predictions_csv: {output_dir / "structured_val_predictions.csv"}
  test_predictions_csv: {output_dir / "structured_test_predictions.csv"}
  run_summary_json: {output_dir / "structured_run_summary.json"}
  model_path: {output_dir / "structured_logistic.pkl"}
""",
        encoding="utf-8",
    )

    status = train(config_path)

    assert status == 0
    metrics = pd.read_csv(output_dir / "structured_baseline_metrics.csv")
    table = pd.read_csv(table_dir / "table_structured_baseline_results.csv")
    predictions = pd.read_csv(output_dir / "structured_test_predictions.csv")
    assert set(metrics["label"]) == {"macro", *labels}
    assert table["label"].eq("macro").all()
    assert {"ecg_id", "NORM_true", "NORM_prob", "HYP_true", "HYP_prob"}.issubset(predictions.columns)
    assert (output_dir / "structured_logistic.pkl").exists()


def test_structured_baseline_requires_nonempty_feature_set(tmp_path: Path) -> None:
    from src.training.train_structured import _load_dataset

    features_csv = tmp_path / "features.csv"
    index_csv = tmp_path / "index.csv"
    pd.DataFrame({"ecg_id": [1]}).to_csv(features_csv, index=False)
    pd.DataFrame({"ecg_id": [1], "split": ["train"], "NORM": [1]}).to_csv(index_csv, index=False)

    paths = {
        "features_csv": features_csv,
        "index_csv": index_csv,
        "feature_names_txt": tmp_path / "missing.txt",
    }
    try:
        _load_dataset(paths, ["NORM"])
    except ValueError as exc:
        assert "No structured feature columns" in str(exc)
    else:
        raise AssertionError("Expected empty structured feature set to fail.")
