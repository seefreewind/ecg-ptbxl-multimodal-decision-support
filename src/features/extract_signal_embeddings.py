from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import wfdb
from torch.utils.data import DataLoader, Dataset

from src.models.signal_resnet import SignalResNet
from src.utils.io import ensure_dir, load_yaml, project_root_from_config, resolve_path, safe_to_csv


class PTBXLEmbeddingDataset(Dataset):
    def __init__(self, csv_path: Path, records_base_dir: Path) -> None:
        self.df = pd.read_csv(csv_path)
        self.records_base_dir = records_base_dir
        required = ["ecg_id", "filename_lr"]
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            raise ValueError(f"{csv_path} is missing required columns: {missing}")

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, idx: int) -> tuple[int, torch.Tensor]:
        row = self.df.iloc[idx]
        signal, _ = wfdb.rdsamp(str(self.records_base_dir / str(row["filename_lr"])))
        x = np.asarray(signal, dtype=np.float32).T
        mean = x.mean(axis=1, keepdims=True)
        std = x.std(axis=1, keepdims=True)
        x = (x - mean) / np.maximum(std, 1e-6)
        return int(row["ecg_id"]), torch.from_numpy(x)


def _auto_device(requested: str) -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _model_from_checkpoint(checkpoint_path: Path, device: torch.device) -> SignalResNet:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    cfg = checkpoint.get("config", {})
    model_cfg = cfg.get("model", {})
    labels = checkpoint.get("labels", cfg.get("data", {}).get("labels", ["NORM", "MI", "STTC", "CD", "HYP"]))
    model = SignalResNet(
        in_channels=int(model_cfg.get("input_channels", 12)),
        num_classes=int(model_cfg.get("num_classes", len(labels))),
        base_channels=int(model_cfg.get("base_channels", 64)),
        blocks_per_stage=tuple(model_cfg.get("blocks_per_stage", [2, 2, 2])),
        dropout=float(model_cfg.get("dropout", 0.2)),
    )
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
        raise RuntimeError(f"Checkpoint load mismatch: missing={sorted(true_missing)} unexpected={unexpected}")
    model.to(device)
    model.eval()
    return model


@torch.no_grad()
def extract_split(model: SignalResNet, csv_path: Path, records_base_dir: Path, out_csv: Path, batch_size: int, num_workers: int, device: torch.device) -> int:
    dataset = PTBXLEmbeddingDataset(csv_path, records_base_dir)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    ids: list[np.ndarray] = []
    embeddings: list[np.ndarray] = []
    for ecg_id, x in loader:
        _logits, emb = model(x.to(device), return_embedding=True)
        ids.append(ecg_id.numpy())
        embeddings.append(emb.cpu().numpy())
    ecg_ids = np.concatenate(ids)
    emb_arr = np.concatenate(embeddings, axis=0)
    if emb_arr.shape[1] <= 5:
        raise ValueError(f"embedding_dim must be > 5, got {emb_arr.shape[1]}")
    if pd.Series(ecg_ids).isna().any():
        raise ValueError(f"Missing ecg_id in {csv_path}")
    if pd.Series(ecg_ids).duplicated().any():
        raise ValueError(f"Duplicate ecg_id in {csv_path}")
    out = pd.DataFrame(
        np.column_stack([ecg_ids.astype(int), emb_arr]),
        columns=["ecg_id"] + [f"emb_{idx:03d}" for idx in range(emb_arr.shape[1])],
    )
    out["ecg_id"] = out["ecg_id"].astype(int)
    safe_to_csv(out, out_csv)
    return int(len(out))


def run(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    cfg = load_yaml(config_path)
    data = cfg.get("data", {})
    runtime = cfg.get("runtime", {})
    output = cfg.get("output", {})
    paths = {
        "train_csv": resolve_path(data.get("train_csv"), root),
        "val_csv": resolve_path(data.get("val_csv"), root),
        "test_csv": resolve_path(data.get("test_csv"), root),
        "records_base_dir": resolve_path(data.get("records_base_dir"), root),
        "checkpoint_path": resolve_path(data.get("checkpoint_path"), root),
        "out_train": resolve_path(output.get("train_csv"), root),
        "out_val": resolve_path(output.get("val_csv"), root),
        "out_test": resolve_path(output.get("test_csv"), root),
        "metadata_json": resolve_path(output.get("metadata_json"), root),
    }
    for key in ["train_csv", "val_csv", "test_csv", "records_base_dir", "checkpoint_path"]:
        if paths[key] is None or not paths[key].exists():
            raise FileNotFoundError(f"Required path missing: {key}={paths[key]}")
    random.seed(2026)
    np.random.seed(2026)
    torch.manual_seed(2026)
    device = _auto_device(str(runtime.get("device", "auto")))
    model = _model_from_checkpoint(paths["checkpoint_path"], device)
    batch_size = int(runtime.get("batch_size", 64))
    num_workers = int(runtime.get("num_workers", 0))
    train_rows = extract_split(model, paths["train_csv"], paths["records_base_dir"], paths["out_train"], batch_size, num_workers, device)
    val_rows = extract_split(model, paths["val_csv"], paths["records_base_dir"], paths["out_val"], batch_size, num_workers, device)
    test_rows = extract_split(model, paths["test_csv"], paths["records_base_dir"], paths["out_test"], batch_size, num_workers, device)
    sample = pd.read_csv(paths["out_train"], nrows=1)
    embedding_dim = len([col for col in sample.columns if col.startswith("emb_")])
    metadata = {
        "checkpoint_path": str(paths["checkpoint_path"]),
        "embedding_layer": "global pooled representation before final classifier",
        "embedding_dim": int(embedding_dim),
        "train_rows": train_rows,
        "val_rows": val_rows,
        "test_rows": test_rows,
        "device_used": str(device),
    }
    ensure_dir(paths["metadata_json"].parent)
    paths["metadata_json"].write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Signal embeddings extracted: dim={embedding_dim} train={train_rows} val={val_rows} test={test_rows}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract strong signal encoder embeddings for fair fusion.")
    parser.add_argument("--config", default="configs/extract_signal_embeddings.yaml")
    args = parser.parse_args()
    raise SystemExit(run(args.config))


if __name__ == "__main__":
    main()
