from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import pandas as pd

from src.training.train_signal import train
from src.utils.io import ensure_dir, load_yaml, project_root_from_config, safe_to_csv


def summarise_repeated_seed_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    macro = metrics[metrics["label"].eq("macro")].copy()
    grouped = macro.groupby(["split", "label"], as_index=False).agg(
        n_seeds=("seed", "nunique"),
        auroc_mean=("auroc", "mean"),
        auroc_std=("auroc", "std"),
        average_precision_mean=("average_precision", "mean"),
        average_precision_std=("average_precision", "std"),
        f1_mean=("f1", "mean"),
        f1_std=("f1", "std"),
    )
    return grouped[
        [
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
    ]


def _write_seed_config(base_config: dict[str, Any], base_path: Path, seed: int, out_dir: Path) -> Path:
    cfg = copy.deepcopy(base_config)
    cfg.setdefault("training", {})
    cfg["training"]["seed"] = seed
    cfg.setdefault("output", {})
    prefix = "signal_strong" if "strong" in base_path.stem else "signal"
    cfg["output"]["metrics_csv"] = str(out_dir / f"seed_{seed}" / f"{prefix}_metrics.csv")
    cfg["output"]["metrics_val_csv"] = str(out_dir / f"seed_{seed}" / f"{prefix}_metrics_val.csv")
    cfg["output"]["metrics_test_csv"] = str(out_dir / f"seed_{seed}" / f"{prefix}_metrics_test.csv")
    cfg["output"]["table_csv"] = str(out_dir / f"seed_{seed}" / f"table_{prefix}_results.csv")
    cfg["output"]["val_predictions_csv"] = str(out_dir / f"seed_{seed}" / f"{prefix}_val_predictions.csv")
    cfg["output"]["test_predictions_csv"] = str(out_dir / f"seed_{seed}" / f"{prefix}_test_predictions.csv")
    cfg["output"]["history_csv"] = str(out_dir / f"seed_{seed}" / f"{prefix}_training_history.csv")
    cfg["output"]["run_summary_json"] = str(out_dir / f"seed_{seed}" / f"{prefix}_run_summary.json")
    cfg["output"]["checkpoint_path"] = str(out_dir / f"seed_{seed}" / f"{prefix}_last.pt")
    cfg["output"]["best_checkpoint_path"] = str(out_dir / f"seed_{seed}" / f"{prefix}_best.pt")
    cfg["output"]["thresholds_json"] = str(out_dir / f"seed_{seed}" / "val_tuned_thresholds.json")
    cfg["output"]["thresholds_table_csv"] = str(out_dir / f"seed_{seed}" / f"table_{prefix}_thresholds.csv")
    cfg["output"]["threshold_comparison_csv"] = str(out_dir / f"seed_{seed}" / f"table_{prefix}_threshold_comparison.csv")

    seed_config = out_dir / f"seed_{seed}" / base_path.name
    ensure_dir(seed_config.parent)
    import yaml

    seed_config.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    return seed_config


def run_repeated(config_path: str | Path, seeds: list[int], output_dir: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    out_dir = Path(output_dir)
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    ensure_dir(out_dir)
    base_config = load_yaml(config_path)

    frames: list[pd.DataFrame] = []
    for seed in seeds:
        seed_config = _write_seed_config(base_config, config_path, seed, out_dir)
        status = train(seed_config)
        if status != 0:
            return status
        prefix = "signal_strong" if "strong" in config_path.stem else "signal"
        metrics_path = out_dir / f"seed_{seed}" / f"{prefix}_metrics.csv"
        metrics = pd.read_csv(metrics_path)
        metrics.insert(0, "seed", seed)
        frames.append(metrics)

    all_metrics = pd.concat(frames, ignore_index=True)
    summary = summarise_repeated_seed_metrics(all_metrics)
    out_prefix = "signal_strong" if "strong" in config_path.stem else "signal"
    metrics_name = f"{out_prefix}_repeated_seed_metrics.csv"
    summary_name = f"{out_prefix}_repeated_seed_summary.csv"
    table_name = f"table_{out_prefix}_repeated_seed_summary.csv"
    safe_to_csv(all_metrics, out_dir / metrics_name)
    safe_to_csv(summary, out_dir / summary_name)
    safe_to_csv(summary, root / "tables" / table_name)
    print(f"Repeated-seed metrics: {out_dir / metrics_name}")
    print(f"Repeated-seed summary: {out_dir / summary_name}")
    print(f"Repeated-seed table: {root / 'tables' / table_name}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeated-seed PTB-XL signal-only baseline.")
    parser.add_argument("--config", default="configs/model_signal_resnet.yaml")
    parser.add_argument("--seeds", default="2026,2027,2028")
    parser.add_argument("--output-dir", default="results/internal/repeated_signal")
    args = parser.parse_args()
    seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]
    raise SystemExit(run_repeated(args.config, seeds, args.output_dir))


if __name__ == "__main__":
    main()
