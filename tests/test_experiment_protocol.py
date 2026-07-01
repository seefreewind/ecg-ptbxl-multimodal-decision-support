from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def test_official_fold_split_files_follow_protocol() -> None:
    train = pd.read_csv("data/processed/ptbxl_labels.csv")
    splits = {
        "train": pd.read_csv("data/splits/ptbxl_train.csv"),
        "val": pd.read_csv("data/splits/ptbxl_val.csv"),
        "test": pd.read_csv("data/splits/ptbxl_test.csv"),
    }
    fold_by_id = train.set_index("ecg_id")["strat_fold"]

    assert set(fold_by_id.loc[splits["train"]["ecg_id"]].unique()).issubset(set(range(1, 9)))
    assert set(fold_by_id.loc[splits["val"]["ecg_id"]].unique()) == {9}
    assert set(fold_by_id.loc[splits["test"]["ecg_id"]].unique()) == {10}


def test_strong_config_is_not_limited_to_200_batches() -> None:
    config = yaml.safe_load(Path("configs/model_signal_resnet_strong.yaml").read_text())

    assert config["training"]["max_train_batches_per_epoch"] is None
    assert config["training"]["max_eval_batches"] is None
    assert config["training"]["device"] == "auto"


def test_train_signal_can_read_strong_style_config(tmp_path: Path) -> None:
    from src.training.train_signal import train

    config = yaml.safe_load(Path("configs/model_signal_resnet_strong.yaml").read_text())
    config["model"]["base_channels"] = 4
    config["model"]["blocks_per_stage"] = [1, 1]
    config["training"]["epochs"] = 1
    config["training"]["batch_size"] = 2
    config["training"]["num_workers"] = 0
    config["training"]["device"] = "cpu"
    config["training"]["dry_run"] = True
    config["training"]["max_train_batches_per_epoch"] = 1
    config["training"]["max_eval_batches"] = 1
    config["output"] = {
        "metrics_csv": str(tmp_path / "metrics.csv"),
        "metrics_val_csv": str(tmp_path / "metrics_val.csv"),
        "metrics_test_csv": str(tmp_path / "metrics_test.csv"),
        "table_csv": str(tmp_path / "table.csv"),
        "val_predictions_csv": str(tmp_path / "val_predictions.csv"),
        "test_predictions_csv": str(tmp_path / "test_predictions.csv"),
        "history_csv": str(tmp_path / "history.csv"),
        "run_summary_json": str(tmp_path / "summary.json"),
        "checkpoint_path": str(tmp_path / "last.pt"),
        "best_checkpoint_path": str(tmp_path / "best.pt"),
        "thresholds_json": str(tmp_path / "thresholds.json"),
        "thresholds_table_csv": str(tmp_path / "thresholds.csv"),
        "threshold_comparison_csv": str(tmp_path / "threshold_comparison.csv"),
    }
    config_path = tmp_path / "strong_smoke.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    assert train(config_path) == 0
    assert (tmp_path / "best.pt").exists()
    assert (tmp_path / "thresholds.json").exists()
    comparison = pd.read_csv(tmp_path / "threshold_comparison.csv")
    assert set(comparison["split"]) == {"val", "test"}
    assert set(comparison["threshold_mode"]) == {"default_0.5", "validation_tuned"}
