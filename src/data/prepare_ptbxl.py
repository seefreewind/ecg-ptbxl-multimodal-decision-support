from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from src.data.label_mapping import DEFAULT_SUPERCLASSES, build_ptbxl_superclass_labels
from src.utils.io import ensure_dir, load_yaml, project_root_from_config, resolve_path, safe_to_csv


def _paths(config: dict[str, Any], root: Path) -> dict[str, Path | None]:
    ptbxl = config.get("ptbxl", {})
    output = config.get("output", {})
    return {
        "metadata_csv": resolve_path(ptbxl.get("metadata_csv"), root),
        "scp_statements_csv": resolve_path(ptbxl.get("scp_statements_csv"), root),
        "processed_dir": resolve_path(output.get("processed_dir", "data/processed"), root),
        "split_dir": resolve_path(output.get("split_dir", "data/splits"), root),
        "tables_dir": resolve_path(output.get("tables_dir", "tables"), root),
    }


def _read_scp_statements(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, index_col=0)
    except Exception:
        return pd.read_csv(path)


def _require_file(path: Path | None, label: str) -> Path:
    if path is None or not path.exists():
        raise FileNotFoundError(f"{label} not found. Please place it at: {path}")
    return path


def _write_status(tables_dir: Path, status: str, detail: str) -> None:
    safe_to_csv(
        pd.DataFrame([{"stage": "prepare_ptbxl", "status": status, "detail": detail}]),
        tables_dir / "table_prepare_ptbxl_status.csv",
    )


def _write_split_files(full_df: pd.DataFrame, split_dir: Path, classes: list[str]) -> dict[str, int]:
    split_columns = ["ecg_id", "filename_lr", "filename_hr"] + classes
    split_defs = {
        "train": full_df["strat_fold"].isin(list(range(1, 9))),
        "val": full_df["strat_fold"].eq(9),
        "test": full_df["strat_fold"].eq(10),
    }
    counts: dict[str, int] = {}
    for split, mask in split_defs.items():
        subset = full_df.loc[mask, split_columns]
        counts[split] = int(len(subset))
        if subset.empty:
            raise ValueError(f"Official fold split '{split}' is empty. Check strat_fold values before generating processed files.")
        safe_to_csv(subset, split_dir / f"ptbxl_{split}.csv")
    return counts


def prepare(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    paths = _paths(config, root)
    processed_dir = ensure_dir(paths["processed_dir"])
    split_dir = ensure_dir(paths["split_dir"])
    tables_dir = ensure_dir(paths["tables_dir"])
    classes = config.get("task", {}).get("diagnostic_superclasses", DEFAULT_SUPERCLASSES)

    try:
        metadata_path = _require_file(paths["metadata_csv"], "PTB-XL metadata CSV")
        scp_path = _require_file(paths["scp_statements_csv"], "PTB-XL scp_statements CSV")

        metadata_df = pd.read_csv(metadata_path)
        scp_df = _read_scp_statements(scp_path)
        required_columns = ["ecg_id", "filename_lr", "filename_hr", "strat_fold", "scp_codes"]
        missing_columns = [col for col in required_columns if col not in metadata_df.columns]
        if missing_columns:
            raise ValueError(f"PTB-XL metadata is missing required columns: {missing_columns}")

        labels_df = build_ptbxl_superclass_labels(metadata_df, scp_df, classes=classes)
        output_columns = ["ecg_id", "filename_lr", "filename_hr", "strat_fold"]
        full_df = metadata_df[output_columns].merge(labels_df, on="ecg_id", how="left")
        for label in classes:
            full_df[label] = full_df[label].fillna(0).astype(int)

        if full_df.empty:
            raise ValueError("PTB-XL metadata contains zero rows; processed files were not generated.")
        if full_df[classes].sum().sum() == 0:
            raise ValueError("No diagnostic superclass labels were generated. Check scp_statements.csv diagnostic_class mapping.")

        safe_to_csv(full_df[output_columns + classes], processed_dir / "ptbxl_labels.csv")
        split_counts = _write_split_files(full_df, split_dir, classes)
        _write_status(tables_dir, "success", f"generated labels and splits: {split_counts}")

        print("Stage 1 PTB-XL label and split preparation completed.")
        print("Status: success")
        print(f"Labels: {processed_dir / 'ptbxl_labels.csv'}")
        print(f"Splits: {split_dir}")
        return 0
    except Exception as exc:
        _write_status(tables_dir, "failed", str(exc))
        print("Stage 1 PTB-XL label and split preparation failed.")
        print("Status: failed")
        print(str(exc))
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare PTB-XL labels and official folds without training models.")
    parser.add_argument("--config", required=True, help="Path to configs/data_ptbxl.yaml")
    args = parser.parse_args()
    raise SystemExit(prepare(args.config))


if __name__ == "__main__":
    main()
