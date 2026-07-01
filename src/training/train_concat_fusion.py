from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import wfdb
from torch.utils.data import DataLoader, Dataset

from src.models.signal_resnet import SignalResNet
from src.training.metrics import compute_multilabel_metrics
from src.training.train_structured import _apply_standardizer, _fit_models, _fit_standardizer, _predict_prob
from src.utils.io import ensure_dir, load_yaml, project_root_from_config, resolve_path, safe_to_csv


class SignalFeatureDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, records_base_dir: Path, labels: list[str]) -> None:
        self.df = frame.reset_index(drop=True)
        self.records_base_dir = records_base_dir
        self.labels = labels

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        row = self.df.iloc[idx]
        signal, _ = wfdb.rdsamp(str(self.records_base_dir / str(row["filename_lr"])))
        x = np.asarray(signal, dtype=np.float32).T
        mean = x.mean(axis=1, keepdims=True)
        std = x.std(axis=1, keepdims=True)
        x = (x - mean) / np.maximum(std, 1e-6)
        y = row[self.labels].to_numpy(dtype=np.float32)
        return torch.from_numpy(x), torch.from_numpy(y)


def _paths(config: dict[str, Any], root: Path) -> dict[str, Path]:
    data = config.get("data", {})
    output = config.get("output", {})
    signal_features = data.get("signal_feature_csvs", {}) or {}
    return {
        "features_csv": resolve_path(data.get("features_csv", "data/processed/ptbxl_structured_features.csv"), root),
        "index_csv": resolve_path(data.get("index_csv", "data/processed/ptbxl_multimodal_index.csv"), root),
        "feature_names_txt": resolve_path(data.get("feature_names_txt", "data/processed/structured_feature_names.txt"), root),
        "records_base_dir": resolve_path(data.get("records_base_dir", "data/raw/ptbxl"), root),
        "signal_checkpoint_path": resolve_path(data.get("signal_checkpoint_path", "results/internal/signal_resnet.pt"), root),
        "signal_train_features_csv": resolve_path(signal_features.get("train"), root),
        "signal_val_features_csv": resolve_path(signal_features.get("val"), root),
        "signal_test_features_csv": resolve_path(signal_features.get("test"), root),
        "generated_signal_train_csv": resolve_path(output.get("generated_signal_train_csv", "results/internal/concat_fusion_signal_train_features.csv"), root),
        "generated_signal_val_csv": resolve_path(output.get("generated_signal_val_csv", "results/internal/concat_fusion_signal_val_features.csv"), root),
        "generated_signal_test_csv": resolve_path(output.get("generated_signal_test_csv", "results/internal/concat_fusion_signal_test_features.csv"), root),
        "metrics_csv": resolve_path(output.get("metrics_csv", "results/internal/concat_fusion_metrics.csv"), root),
        "table_csv": resolve_path(output.get("table_csv", "tables/table_concat_fusion_results.csv"), root),
        "val_predictions_csv": resolve_path(output.get("val_predictions_csv", "results/internal/concat_fusion_val_predictions.csv"), root),
        "test_predictions_csv": resolve_path(output.get("test_predictions_csv", "results/internal/concat_fusion_test_predictions.csv"), root),
        "run_summary_json": resolve_path(output.get("run_summary_json", "results/internal/concat_fusion_run_summary.json"), root),
        "model_path": resolve_path(output.get("model_path", "results/internal/concat_fusion_logistic.pkl"), root),
    }


def _read_feature_names(path: Path | None, features: pd.DataFrame) -> list[str]:
    if path is not None and path.exists():
        names = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        names = [name for name in names if name in features.columns and name != "ecg_id"]
        if names:
            return names
    return [col for col in features.columns if col != "ecg_id"]


def _load_base_frames(paths: dict[str, Path], labels: list[str]) -> tuple[pd.DataFrame, list[str]]:
    features = pd.read_csv(paths["features_csv"])
    index = pd.read_csv(paths["index_csv"])
    feature_names = _read_feature_names(paths.get("feature_names_txt"), features)
    required = ["ecg_id", "split", "filename_lr"] + labels
    missing = [col for col in required if col not in index.columns]
    if missing:
        raise ValueError(f"{paths['index_csv']} is missing required columns: {missing}")
    merged = index[required].merge(features[["ecg_id"] + feature_names], on="ecg_id", how="inner")
    if merged.empty:
        raise ValueError("No rows remain after joining structured features and multimodal index.")
    return merged, feature_names


def _auto_device(requested: str) -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _load_signal_model(checkpoint_path: Path, device: torch.device) -> SignalResNet:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    cfg = checkpoint.get("config", {})
    model_cfg = cfg.get("model", {})
    labels = checkpoint.get("labels", cfg.get("data", {}).get("labels", ["NORM", "MI", "STTC", "CD", "HYP"]))
    model = SignalResNet(
        in_channels=int(model_cfg.get("input_channels", 12)),
        num_classes=int(model_cfg.get("num_classes", len(labels))),
        base_channels=int(model_cfg.get("base_channels", 16)),
        blocks_per_stage=tuple(model_cfg.get("blocks_per_stage", [1, 1, 1])),
        dropout=float(model_cfg.get("dropout", 0.1)),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model


@torch.no_grad()
def _extract_signal_probability_features(
    model: SignalResNet,
    frame: pd.DataFrame,
    records_base_dir: Path,
    labels: list[str],
    device: torch.device,
    batch_size: int,
    num_workers: int,
) -> pd.DataFrame:
    dataset = SignalFeatureDataset(frame, records_base_dir, labels)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    probs: list[np.ndarray] = []
    for x, _y in loader:
        logits = model(x.to(device))
        probs.append(torch.sigmoid(logits).cpu().numpy())
    out = frame[["ecg_id", "split"]].reset_index(drop=True).copy()
    p = np.concatenate(probs, axis=0)
    for idx, label in enumerate(labels):
        out[f"signal_{label}_prob"] = p[:, idx]
    return out


def _load_or_generate_signal_features(
    paths: dict[str, Path],
    df: pd.DataFrame,
    labels: list[str],
    training: dict[str, Any],
) -> pd.DataFrame:
    provided = {
        "train": paths.get("signal_train_features_csv"),
        "val": paths.get("signal_val_features_csv"),
        "test": paths.get("signal_test_features_csv"),
    }
    if all(path is not None and path.exists() for path in provided.values()):
        frames = [pd.read_csv(provided[split]) for split in ["train", "val", "test"]]
        return pd.concat(frames, ignore_index=True)

    checkpoint_path = paths["signal_checkpoint_path"]
    if checkpoint_path is None or not checkpoint_path.exists():
        raise FileNotFoundError(f"Signal checkpoint missing for concat fusion: {checkpoint_path}")
    device = _auto_device(str(training.get("device", "cpu")))
    model = _load_signal_model(checkpoint_path, device)
    batch_size = int(training.get("signal_batch_size", training.get("batch_size", 64)))
    num_workers = int(training.get("num_workers", 0))
    generated = []
    output_paths = {
        "train": paths["generated_signal_train_csv"],
        "val": paths["generated_signal_val_csv"],
        "test": paths["generated_signal_test_csv"],
    }
    for split in ["train", "val", "test"]:
        split_frame = df[df["split"].eq(split)].copy()
        signal_features = _extract_signal_probability_features(
            model,
            split_frame,
            paths["records_base_dir"],
            labels,
            device,
            batch_size,
            num_workers,
        )
        safe_to_csv(signal_features, output_paths[split])
        generated.append(signal_features)
    return pd.concat(generated, ignore_index=True)


def _build_xy(df: pd.DataFrame, labels: list[str], feature_names: list[str], split: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    part = df[df["split"].eq(split)].copy()
    if part.empty:
        raise ValueError(f"No rows found for split={split}.")
    x = part[feature_names].replace([np.inf, -np.inf], np.nan).to_numpy(dtype=float)
    y = part[labels].to_numpy(dtype=np.float32)
    return part[["ecg_id", "split"]].reset_index(drop=True), x, y


def train(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    paths = _paths(config, root)
    labels = list(config.get("data", {}).get("labels", ["NORM", "MI", "STTC", "CD", "HYP"]))
    training = config.get("training", {})

    base, structured_feature_names = _load_base_frames(paths, labels)
    signal_features = _load_or_generate_signal_features(paths, base, labels, training)
    signal_feature_names = [f"signal_{label}_prob" for label in labels]
    missing_signal = [col for col in ["ecg_id"] + signal_feature_names if col not in signal_features.columns]
    if missing_signal:
        raise ValueError(f"Signal feature table missing required columns: {missing_signal}")

    df = base.merge(signal_features[["ecg_id"] + signal_feature_names], on="ecg_id", how="inner")
    fusion_feature_names = structured_feature_names + signal_feature_names
    train_meta, x_train_raw, y_train = _build_xy(df, labels, fusion_feature_names, "train")
    val_meta, x_val_raw, y_val = _build_xy(df, labels, fusion_feature_names, "val")
    test_meta, x_test_raw, y_test = _build_xy(df, labels, fusion_feature_names, "test")

    from sklearn.impute import SimpleImputer

    imputer = SimpleImputer(strategy=str(training.get("imputation_strategy", "median")))
    x_train_imputed = imputer.fit_transform(x_train_raw)
    mean, std = _fit_standardizer(x_train_imputed)
    x_train = _apply_standardizer(x_train_imputed, mean, std)
    x_val = _apply_standardizer(imputer.transform(x_val_raw), mean, std)
    x_test = _apply_standardizer(imputer.transform(x_test_raw), mean, std)

    model_cfg = dict(config.get("model", {}))
    model_cfg.setdefault("random_state", int(training.get("seed", 2026)))
    models = _fit_models(x_train, y_train, labels, model_cfg)
    p_val = _predict_prob(models, x_val)
    p_test = _predict_prob(models, x_test)

    metrics = pd.concat(
        [
            compute_multilabel_metrics(y_val, p_val, labels, split="val"),
            compute_multilabel_metrics(y_test, p_test, labels, split="test"),
        ],
        ignore_index=True,
    )
    safe_to_csv(metrics, paths["metrics_csv"])
    safe_to_csv(metrics[metrics["label"].eq("macro")], paths["table_csv"])
    safe_to_csv(_prediction_frame(val_meta, y_val, p_val, labels), paths["val_predictions_csv"])
    safe_to_csv(_prediction_frame(test_meta, y_test, p_test, labels), paths["test_predictions_csv"])

    ensure_dir(paths["model_path"].parent)
    with paths["model_path"].open("wb") as fh:
        pickle.dump(
            {
                "imputer": imputer,
                "standardizer_mean": mean,
                "standardizer_std": std,
                "models": models,
                "labels": labels,
                "structured_feature_names": structured_feature_names,
                "signal_feature_names": signal_feature_names,
                "config": config,
            },
            fh,
        )

    summary = {
        "config_path": str(config_path),
        "labels": labels,
        "n_train": int(len(train_meta)),
        "n_val": int(len(val_meta)),
        "n_test": int(len(test_meta)),
        "n_structured_features": int(len(structured_feature_names)),
        "n_signal_features": int(len(signal_feature_names)),
        "n_fusion_features": int(len(fusion_feature_names)),
        "metrics_csv": str(paths["metrics_csv"]),
        "table_csv": str(paths["table_csv"]),
        "model_path": str(paths["model_path"]),
    }
    ensure_dir(paths["run_summary_json"].parent)
    paths["run_summary_json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print("Concat fusion baseline completed.")
    print(f"Rows: train={len(train_meta)} val={len(val_meta)} test={len(test_meta)}")
    print(f"Features: structured={len(structured_feature_names)} signal={len(signal_feature_names)}")
    print(f"Metrics: {paths['metrics_csv']}")
    print(f"Table: {paths['table_csv']}")
    return 0


def _prediction_frame(meta: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray, labels: list[str]) -> pd.DataFrame:
    out = meta.copy()
    for idx, label in enumerate(labels):
        out[f"{label}_true"] = y_true[:, idx].astype(int)
        out[f"{label}_prob"] = y_prob[:, idx]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Train simple PTB-XL concat fusion baseline.")
    parser.add_argument("--config", default="configs/model_concat_fusion.yaml", help="Path to concat fusion config")
    args = parser.parse_args()
    raise SystemExit(train(args.config))


if __name__ == "__main__":
    main()
