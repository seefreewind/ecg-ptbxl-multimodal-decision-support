from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

from src.utils.io import ensure_dir, load_yaml, project_root_from_config, resolve_path, safe_to_csv


def _feature_names(path: Path, features: pd.DataFrame) -> list[str]:
    if path.exists():
        names = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        names = [name for name in names if name in features.columns and name != "ecg_id"]
        if names:
            return names
    return [col for col in features.columns if col != "ecg_id"]


def _fit_standardizer(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(x, axis=0)
    std = np.std(x, axis=0)
    std = np.where(std < 1e-8, 1.0, std)
    return mean, std


def _transform_standardizer(x: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return (x - mean) / std


def _load_split_embeddings(paths: dict[str, Path]) -> pd.DataFrame:
    frames = []
    for split, key in [("train", "signal_train_csv"), ("val", "signal_val_csv"), ("test", "signal_test_csv")]:
        df = pd.read_csv(paths[key])
        df["split"] = split
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _prepare_raw(paths: dict[str, Path], labels: list[str]) -> tuple[pd.DataFrame, list[str], list[str], int]:
    embeddings = _load_split_embeddings(paths)
    emb_cols = [col for col in embeddings.columns if col.startswith("emb_")]
    if len(emb_cols) <= 5:
        raise ValueError(f"signal embedding dim must be > 5, got {len(emb_cols)}")
    if embeddings["ecg_id"].isna().any() or embeddings["ecg_id"].duplicated().any():
        raise ValueError("Signal embeddings contain missing or duplicate ecg_id values.")

    structured = pd.read_csv(paths["structured_features_csv"])
    struct_names = _feature_names(paths["structured_feature_names_txt"], structured)
    index = pd.read_csv(paths["multimodal_index_csv"])
    required = ["ecg_id", "split"] + labels
    missing = [col for col in required if col not in index.columns]
    if missing:
        raise ValueError(f"{paths['multimodal_index_csv']} is missing required columns: {missing}")
    raw_struct_missing = int(structured[struct_names].isna().sum().sum())
    base = index[required].merge(embeddings[["ecg_id"] + emb_cols], on="ecg_id", how="inner")
    base = base.merge(structured[["ecg_id"] + struct_names], on="ecg_id", how="inner")
    for split, expected in [("train", 17418), ("val", 2183), ("test", 2198)]:
        found = int(base["split"].eq(split).sum())
        if found != expected:
            raise ValueError(f"{split} rows mismatch: expected {expected}, got {found}")
    return base, emb_cols, struct_names, raw_struct_missing


def _prefix_frame(meta: pd.DataFrame, signal_arr: np.ndarray, struct_arr: np.ndarray, signal_cols: list[str], struct_cols: list[str], labels: list[str]) -> pd.DataFrame:
    signal_df = pd.DataFrame(signal_arr, columns=[f"signal_emb_{idx:03d}" for idx, _col in enumerate(signal_cols)])
    struct_df = pd.DataFrame(struct_arr, columns=[f"struct_{col}" for col in struct_cols])
    label_df = meta[labels].astype(int).reset_index(drop=True)
    return pd.concat([meta[["ecg_id"]].reset_index(drop=True), signal_df, struct_df, label_df, meta[["split"]].reset_index(drop=True)], axis=1)


def run(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    cfg = load_yaml(config_path)
    data = cfg.get("data", {})
    output = cfg.get("output", {})
    preprocessing = cfg.get("preprocessing", {})
    paths = {
        "signal_train_csv": resolve_path(data.get("signal_train_csv"), root),
        "signal_val_csv": resolve_path(data.get("signal_val_csv"), root),
        "signal_test_csv": resolve_path(data.get("signal_test_csv"), root),
        "structured_features_csv": resolve_path(data.get("structured_features_csv"), root),
        "multimodal_index_csv": resolve_path(data.get("multimodal_index_csv"), root),
        "structured_feature_names_txt": resolve_path(data.get("structured_feature_names_txt"), root),
        "train_csv": resolve_path(output.get("train_csv"), root),
        "val_csv": resolve_path(output.get("val_csv"), root),
        "test_csv": resolve_path(output.get("test_csv"), root),
        "manifest_csv": resolve_path(output.get("manifest_csv"), root),
        "preprocessing_artifact": resolve_path(output.get("preprocessing_artifact"), root),
        "report_md": resolve_path(output.get("report_md"), root),
    }
    for key in ["signal_train_csv", "signal_val_csv", "signal_test_csv", "structured_features_csv", "multimodal_index_csv", "structured_feature_names_txt"]:
        if paths[key] is None or not paths[key].exists():
            raise FileNotFoundError(f"Required path missing: {key}={paths[key]}")
    labels = list(data.get("labels", ["NORM", "MI", "STTC", "CD", "HYP"]))
    raw, signal_cols, struct_cols, raw_struct_missing = _prepare_raw(paths, labels)

    train = raw[raw["split"].eq("train")].copy()
    val = raw[raw["split"].eq("val")].copy()
    test = raw[raw["split"].eq("test")].copy()
    signal_imputer = SimpleImputer(strategy=str(preprocessing.get("imputation_strategy", "median")))
    struct_imputer = SimpleImputer(strategy=str(preprocessing.get("imputation_strategy", "median")))

    x_sig_train = signal_imputer.fit_transform(train[signal_cols].replace([np.inf, -np.inf], np.nan))
    x_struct_train = struct_imputer.fit_transform(train[struct_cols].replace([np.inf, -np.inf], np.nan))
    sig_mean, sig_std = _fit_standardizer(x_sig_train)
    struct_mean, struct_std = _fit_standardizer(x_struct_train)

    def transform(part: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        sig = signal_imputer.transform(part[signal_cols].replace([np.inf, -np.inf], np.nan))
        struct = struct_imputer.transform(part[struct_cols].replace([np.inf, -np.inf], np.nan))
        if bool(preprocessing.get("standardize_signal", True)):
            sig = _transform_standardizer(sig, sig_mean, sig_std)
        if bool(preprocessing.get("standardize_structured", True)):
            struct = _transform_standardizer(struct, struct_mean, struct_std)
        return sig, struct

    train_sig, train_struct = transform(train)
    val_sig, val_struct = transform(val)
    test_sig, test_struct = transform(test)
    outputs = {
        "train": _prefix_frame(train, train_sig, train_struct, signal_cols, struct_cols, labels),
        "val": _prefix_frame(val, val_sig, val_struct, signal_cols, struct_cols, labels),
        "test": _prefix_frame(test, test_sig, test_struct, signal_cols, struct_cols, labels),
    }
    for split, df in outputs.items():
        feature_cols = [col for col in df.columns if col.startswith("signal_emb_") or col.startswith("struct_")]
        if int(df[feature_cols].isna().sum().sum()) != 0:
            raise ValueError(f"Missing values remain after preprocessing for split={split}")
    safe_to_csv(outputs["train"], paths["train_csv"])
    safe_to_csv(outputs["val"], paths["val_csv"])
    safe_to_csv(outputs["test"], paths["test_csv"])

    manifest_rows = [{"feature": f"signal_emb_{idx:03d}", "modality": "signal_embedding", "source_feature": col} for idx, col in enumerate(signal_cols)]
    manifest_rows.extend({"feature": f"struct_{col}", "modality": "structured", "source_feature": col} for col in struct_cols)
    safe_to_csv(pd.DataFrame(manifest_rows), paths["manifest_csv"])

    ensure_dir(paths["preprocessing_artifact"].parent)
    with paths["preprocessing_artifact"].open("wb") as fh:
        pickle.dump(
            {
                "signal_imputer": signal_imputer,
                "structured_imputer": struct_imputer,
                "signal_mean": sig_mean,
                "signal_std": sig_std,
                "structured_mean": struct_mean,
                "structured_std": struct_std,
                "signal_columns": signal_cols,
                "structured_columns": struct_cols,
                "fit_split": "train",
            },
            fh,
        )

    missing_after = sum(int(df[[c for c in df.columns if c.startswith("signal_emb_") or c.startswith("struct_")]].isna().sum().sum()) for df in outputs.values())
    report = f"""# Stage 6A Fair Fusion Dataset Report

## Status

ready

## Dimensions

- signal embedding dim: {len(signal_cols)}
- structured feature dim: {len(struct_cols)}
- total fusion feature dim: {len(signal_cols) + len(struct_cols)}

## Rows

- train rows: {len(outputs['train'])}
- validation rows: {len(outputs['val'])}
- test rows: {len(outputs['test'])}

## Preprocessing

- fit split: train
- signal standardization: {bool(preprocessing.get('standardize_signal', True))}
- structured standardization: {bool(preprocessing.get('standardize_structured', True))}
- missing structured values before imputation: {raw_struct_missing}
- missing values after preprocessing: {missing_after}
- official split preserved: yes
"""
    ensure_dir(paths["report_md"].parent)
    paths["report_md"].write_text(report, encoding="utf-8")
    print(f"Fair fusion dataset built: signal_dim={len(signal_cols)} structured_dim={len(struct_cols)} train={len(outputs['train'])} val={len(outputs['val'])} test={len(outputs['test'])}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Build leakage-safe fair fusion datasets.")
    parser.add_argument("--config", default="configs/fair_fusion_dataset.yaml")
    args = parser.parse_args()
    raise SystemExit(run(args.config))


if __name__ == "__main__":
    main()
