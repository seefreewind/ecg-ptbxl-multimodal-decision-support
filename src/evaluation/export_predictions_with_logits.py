from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from src.models.fusion_mlp import FusionMLP
from src.models.gated_fusion import GatedFusionMLP
from src.models.signal_resnet import SignalResNet
from src.training.train_ablation_mlp import AblationDataset
from src.training.train_fair_concat_fusion import FairFusionDataset
from src.training.train_gated_fusion import GatedFusionDataset
from src.training.train_signal import PTBXLSignalDataset
from src.utils.io import ensure_dir, load_yaml, resolve_path


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]


@dataclass(frozen=True)
class ExportResult:
    model_name: str
    checkpoint_path: str
    val_output_path: str
    test_output_path: str
    val_rows: int
    test_rows: int
    logit_columns: int
    probability_columns: int
    status: str
    notes: str


def _auto_device(requested: str = "auto") -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _load_checkpoint(path: Path, device: torch.device) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing checkpoint: {path}")
    return torch.load(path, map_location=device)


def _load_signal_state(model: SignalResNet, checkpoint: dict[str, Any]) -> None:
    state = checkpoint["model_state_dict"]
    remapped = {}
    for key, value in state.items():
        if key == "head.3.weight":
            remapped["classifier.weight"] = value
        elif key == "head.3.bias":
            remapped["classifier.bias"] = value
        elif key.startswith("head."):
            continue
        else:
            remapped[key] = value
    missing, unexpected = model.load_state_dict(remapped, strict=False)
    allowed_missing = {"classifier.weight", "classifier.bias"} if "classifier.weight" not in remapped else set()
    true_missing = set(missing) - allowed_missing
    if true_missing or unexpected:
        raise RuntimeError(f"Signal checkpoint load mismatch: missing={sorted(true_missing)} unexpected={unexpected}")


def _standard_prediction_frame(meta: pd.DataFrame, y_true: np.ndarray, logits: np.ndarray, labels: list[str]) -> pd.DataFrame:
    probs = 1.0 / (1.0 + np.exp(-logits))
    out = meta.copy().reset_index(drop=True)
    if "split" not in out.columns:
        out.insert(1, "split", "")
    for idx, label in enumerate(labels):
        out[f"y_true_{label}"] = y_true[:, idx].astype(int)
    for idx, label in enumerate(labels):
        out[f"logit_{label}"] = logits[:, idx].astype(np.float32)
    for idx, label in enumerate(labels):
        out[f"prob_{label}"] = probs[:, idx].astype(np.float32)
    ordered = ["ecg_id", "split"] + [f"y_true_{label}" for label in labels] + [f"logit_{label}" for label in labels] + [f"prob_{label}" for label in labels]
    extras = [col for col in out.columns if col not in ordered]
    return out[ordered + extras]


@torch.no_grad()
def _predict_tensor_model(model: torch.nn.Module, dataset: AblationDataset | FairFusionDataset, batch_size: int, device: torch.device, labels: list[str]) -> pd.DataFrame:
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    logits_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    model.eval()
    for x, y in loader:
        logits = model(x.to(device))
        logits_parts.append(logits.detach().cpu().numpy())
        y_parts.append(y.numpy())
    logits_arr = np.concatenate(logits_parts, axis=0)
    y_arr = np.concatenate(y_parts, axis=0)
    meta = dataset.df[["ecg_id", "split"]].copy()
    return _standard_prediction_frame(meta, y_arr, logits_arr, labels)


@torch.no_grad()
def _predict_gated_model(model: GatedFusionMLP, dataset: GatedFusionDataset, batch_size: int, device: torch.device, labels: list[str]) -> pd.DataFrame:
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    logits_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    model.eval()
    for signal_x, structured_x, y in loader:
        logits = model(signal_x.to(device), structured_x.to(device))
        logits_parts.append(logits.detach().cpu().numpy())
        y_parts.append(y.numpy())
    logits_arr = np.concatenate(logits_parts, axis=0)
    y_arr = np.concatenate(y_parts, axis=0)
    meta = dataset.df[["ecg_id", "split"]].copy()
    return _standard_prediction_frame(meta, y_arr, logits_arr, labels)


@torch.no_grad()
def _predict_signal_model(model: SignalResNet, dataset: PTBXLSignalDataset, batch_size: int, device: torch.device, labels: list[str]) -> pd.DataFrame:
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    logits_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    meta_parts: list[pd.DataFrame] = []
    model.eval()
    for batch_idx, (x, y) in enumerate(loader):
        logits = model(x.to(device))
        logits_parts.append(logits.detach().cpu().numpy())
        y_parts.append(y.numpy())
        start = batch_idx * loader.batch_size
        end = start + len(y)
        meta = dataset.df.iloc[start:end][["ecg_id", "filename_lr"]].copy()
        meta.insert(1, "split", "")
        meta_parts.append(meta.reset_index(drop=True))
    logits_arr = np.concatenate(logits_parts, axis=0)
    y_arr = np.concatenate(y_parts, axis=0)
    meta_frame = pd.concat(meta_parts, ignore_index=True)
    return _standard_prediction_frame(meta_frame, y_arr, logits_arr, labels)


def _write_frame(frame: pd.DataFrame, path: Path, split: str) -> None:
    out = frame.copy()
    out["split"] = split
    ensure_dir(path.parent)
    out.to_csv(path, index=False)


def _export_signal(root: Path, device: torch.device) -> ExportResult:
    config = load_yaml(root / "configs/model_signal_resnet_strong.yaml")
    labels = list(config.get("data", {}).get("labels", LABELS))
    checkpoint_path = root / "results/internal/signal_strong/signal_strong_best.pt"
    checkpoint = _load_checkpoint(checkpoint_path, device)
    model_cfg = checkpoint.get("config", config).get("model", {})
    model = SignalResNet(
        in_channels=int(model_cfg.get("input_channels", 12)),
        num_classes=len(labels),
        base_channels=int(model_cfg.get("base_channels", 64)),
        blocks_per_stage=tuple(model_cfg.get("blocks_per_stage", [2, 2, 2])),
        dropout=float(model_cfg.get("dropout", 0.2)),
    ).to(device)
    _load_signal_state(model, checkpoint)
    records_base = resolve_path(config["data"].get("records_base_dir", "data/raw/ptbxl"), root)
    val_ds = PTBXLSignalDataset(resolve_path(config["data"]["val_csv"], root), records_base, labels)
    test_ds = PTBXLSignalDataset(resolve_path(config["data"]["test_csv"], root), records_base, labels)
    batch_size = int(config.get("training", {}).get("batch_size", 64))
    val_out = root / "results/internal/signal_strong/signal_strong_val_predictions_with_logits.csv"
    test_out = root / "results/internal/signal_strong/signal_strong_test_predictions_with_logits.csv"
    _write_frame(_predict_signal_model(model, val_ds, batch_size, device, labels), val_out, "val")
    _write_frame(_predict_signal_model(model, test_ds, batch_size, device, labels), test_out, "test")
    return ExportResult("strong_signal_only", str(checkpoint_path), str(val_out), str(test_out), len(val_ds), len(test_ds), len(labels), len(labels), "exported", "")


def _export_ablation(root: Path, model_name: str, config_path: str, output_dir: str, modality: str, device: torch.device) -> ExportResult:
    config = load_yaml(root / config_path)
    labels = list(config.get("data", {}).get("labels", LABELS))
    checkpoint_path = resolve_path(config["output"]["checkpoint_path"], root)
    checkpoint = _load_checkpoint(checkpoint_path, device)
    val_ds = AblationDataset(resolve_path(config["data"]["val_csv"], root), labels, modality)
    test_ds = AblationDataset(resolve_path(config["data"]["test_csv"], root), labels, modality)
    model_cfg = checkpoint.get("config", config).get("model", {})
    model = FusionMLP(
        input_dim=int(checkpoint.get("input_dim", len(val_ds.feature_cols))),
        hidden_dims=model_cfg.get("hidden_dims", config.get("model", {}).get("hidden_dims", [256, 128])),
        num_classes=len(labels),
        dropout=float(model_cfg.get("dropout", config.get("model", {}).get("dropout", 0.3))),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    batch_size = int(config.get("training", {}).get("batch_size", 128))
    out_dir = root / output_dir
    val_out = out_dir / f"{model_name}_val_predictions_with_logits.csv"
    test_out = out_dir / f"{model_name}_test_predictions_with_logits.csv"
    _write_frame(_predict_tensor_model(model, val_ds, batch_size, device, labels), val_out, "val")
    _write_frame(_predict_tensor_model(model, test_ds, batch_size, device, labels), test_out, "test")
    return ExportResult(model_name, str(checkpoint_path), str(val_out), str(test_out), len(val_ds), len(test_ds), len(labels), len(labels), "exported", "")


def _export_fair_concat(root: Path, device: torch.device) -> ExportResult:
    config = load_yaml(root / "configs/model_fair_concat_mlp.yaml")
    labels = list(config.get("data", {}).get("labels", LABELS))
    checkpoint_path = resolve_path(config["output"]["checkpoint_path"], root)
    checkpoint = _load_checkpoint(checkpoint_path, device)
    val_ds = FairFusionDataset(resolve_path(config["data"]["val_csv"], root), labels)
    test_ds = FairFusionDataset(resolve_path(config["data"]["test_csv"], root), labels)
    model_cfg = checkpoint.get("config", config).get("model", {})
    model = FusionMLP(
        input_dim=int(checkpoint.get("input_dim", len(val_ds.feature_cols))),
        hidden_dims=model_cfg.get("hidden_dims", [512, 256]),
        num_classes=len(labels),
        dropout=float(model_cfg.get("dropout", 0.3)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    batch_size = int(config.get("training", {}).get("batch_size", 128))
    val_out = root / "results/internal/fair_concat/fair_concat_val_predictions_with_logits.csv"
    test_out = root / "results/internal/fair_concat/fair_concat_test_predictions_with_logits.csv"
    _write_frame(_predict_tensor_model(model, val_ds, batch_size, device, labels), val_out, "val")
    _write_frame(_predict_tensor_model(model, test_ds, batch_size, device, labels), test_out, "test")
    return ExportResult("fair_concat_mlp", str(checkpoint_path), str(val_out), str(test_out), len(val_ds), len(test_ds), len(labels), len(labels), "exported", "")


def _export_gated(root: Path, device: torch.device) -> ExportResult:
    config = load_yaml(root / "configs/model_gated_fusion.yaml")
    labels = list(config.get("data", {}).get("labels", LABELS))
    checkpoint_path = resolve_path(config["output"]["checkpoint_path"], root)
    checkpoint = _load_checkpoint(checkpoint_path, device)
    val_ds = GatedFusionDataset(resolve_path(config["data"]["val_csv"], root), labels)
    test_ds = GatedFusionDataset(resolve_path(config["data"]["test_csv"], root), labels)
    model_cfg = checkpoint.get("config", config).get("model", {})
    model = GatedFusionMLP(
        signal_dim=int(checkpoint.get("signal_dim", len(val_ds.signal_cols))),
        structured_dim=int(checkpoint.get("structured_dim", len(val_ds.structured_cols))),
        hidden_dim=int(model_cfg.get("hidden_dim", 256)),
        classifier_hidden_dim=int(model_cfg.get("classifier_hidden_dim", 256)),
        num_classes=len(labels),
        dropout=float(model_cfg.get("dropout", 0.3)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    batch_size = int(config.get("training", {}).get("batch_size", 128))
    val_out = root / "results/internal/gated_fusion/gated_fusion_val_predictions_with_logits.csv"
    test_out = root / "results/internal/gated_fusion/gated_fusion_test_predictions_with_logits.csv"
    _write_frame(_predict_gated_model(model, val_ds, batch_size, device, labels), val_out, "val")
    _write_frame(_predict_gated_model(model, test_ds, batch_size, device, labels), test_out, "test")
    return ExportResult("gated_fusion_mlp", str(checkpoint_path), str(val_out), str(test_out), len(val_ds), len(test_ds), len(labels), len(labels), "exported", "")


def export_main_model_logits(root: str | Path = ".", device_name: str = "auto") -> pd.DataFrame:
    root_path = Path(root).resolve()
    device = _auto_device(device_name)
    results = [
        _export_signal(root_path, device),
        _export_ablation(root_path, "signal_embedding_mlp", "configs/model_signal_embedding_mlp.yaml", "results/internal/signal_embedding_mlp", "signal_embedding", device),
        _export_ablation(root_path, "structured_mlp", "configs/model_structured_mlp.yaml", "results/internal/structured_mlp", "structured", device),
        _export_fair_concat(root_path, device),
        _export_gated(root_path, device),
    ]
    summary = pd.DataFrame([result.__dict__ for result in results])
    out_path = root_path / "results/calibration/logit_export_summary.csv"
    ensure_dir(out_path.parent)
    summary.to_csv(out_path, index=False)
    (root_path / "results/calibration/logit_export_summary.json").write_text(json.dumps(summary.to_dict("records"), indent=2) + "\n")
    return summary


def main() -> None:
    summary = export_main_model_logits()
    print(summary[["model_name", "status", "val_rows", "test_rows"]].to_string(index=False))


if __name__ == "__main__":
    main()
