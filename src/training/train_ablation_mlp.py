from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.evaluation.evaluator import evaluate_multilabel_predictions
from src.models.fusion_mlp import FusionMLP
from src.training.thresholds import save_thresholds, tune_per_class_thresholds
from src.utils.io import ensure_dir, load_yaml, project_root_from_config, resolve_path, safe_to_csv


class AblationDataset(Dataset):
    def __init__(self, csv_path: Path, labels: list[str], modality: str, expected_structured_dim: int = 531) -> None:
        self.df = pd.read_csv(csv_path)
        self.labels = labels
        if modality == "signal_embedding":
            self.feature_cols = [col for col in self.df.columns if col.startswith("signal_emb_")]
        elif modality == "structured":
            self.feature_cols = [col for col in self.df.columns if col.startswith("struct_")]
        else:
            raise ValueError(f"Unsupported ablation modality: {modality}")
        missing = [col for col in ["ecg_id", "split"] + labels if col not in self.df.columns]
        if missing:
            raise ValueError(f"{csv_path} is missing required columns: {missing}")
        if modality == "signal_embedding" and len(self.feature_cols) <= 5:
            raise ValueError(f"Signal ablation requires high-dimensional embeddings, got {len(self.feature_cols)}")
        if modality == "structured" and len(self.feature_cols) != expected_structured_dim:
            raise ValueError(f"Structured ablation expected {expected_structured_dim} features, got {len(self.feature_cols)}")

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        row = self.df.iloc[idx]
        x = row[self.feature_cols].to_numpy(dtype=np.float32)
        y = row[self.labels].to_numpy(dtype=np.float32)
        return torch.from_numpy(x), torch.from_numpy(y)


def _paths(config: dict[str, Any], root: Path) -> dict[str, Path]:
    data = config.get("data", {})
    output = config.get("output", {})
    return {
        "train_csv": resolve_path(data.get("train_csv"), root),
        "val_csv": resolve_path(data.get("val_csv"), root),
        "test_csv": resolve_path(data.get("test_csv"), root),
        "val_predictions_csv": resolve_path(output.get("val_predictions_csv"), root),
        "test_predictions_csv": resolve_path(output.get("test_predictions_csv"), root),
        "history_csv": resolve_path(output.get("history_csv"), root),
        "metrics_val_csv": resolve_path(output.get("metrics_val_csv"), root),
        "metrics_test_csv": resolve_path(output.get("metrics_test_csv"), root),
        "thresholds_json": resolve_path(output.get("thresholds_json"), root),
        "run_summary_json": resolve_path(output.get("run_summary_json"), root),
        "checkpoint_path": resolve_path(output.get("checkpoint_path"), root),
        "table_csv": resolve_path(output.get("table_csv"), root),
        "threshold_comparison_csv": resolve_path(output.get("threshold_comparison_csv"), root),
    }


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _auto_device(requested: str) -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _loader(dataset: Dataset, batch_size: int, shuffle: bool) -> DataLoader:
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=0)


def _run_epoch(model: nn.Module, loader: DataLoader, criterion: nn.Module, optimizer: torch.optim.Optimizer, device: torch.device) -> float:
    model.train()
    losses = []
    for x, y in loader:
        x = x.to(device)
        y = y.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses)) if losses else float("nan")


@torch.no_grad()
def _predict(model: nn.Module, dataset: AblationDataset, loader: DataLoader, device: torch.device, labels: list[str]) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    model.eval()
    probs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    for x, y in loader:
        logits = model(x.to(device))
        probs.append(torch.sigmoid(logits).cpu().numpy())
        ys.append(y.numpy())
    y_true = np.concatenate(ys, axis=0)
    y_prob = np.concatenate(probs, axis=0)
    meta = dataset.df[["ecg_id", "split"]].reset_index(drop=True).copy()
    for idx, label in enumerate(labels):
        meta[f"{label}_true"] = y_true[:, idx].astype(int)
        meta[f"{label}_prob"] = y_prob[:, idx]
    return y_true, y_prob, meta


def _threshold_comparison(y_true: np.ndarray, y_prob: np.ndarray, labels: list[str], split: str, tuned: dict[str, float], model_name: str) -> pd.DataFrame:
    rows = []
    for mode, thresholds in [("default_0.5", None), ("validation_tuned", tuned)]:
        evaluated = evaluate_multilabel_predictions(y_true, y_prob, thresholds=thresholds, label_names=labels, split_name=split, model_name=model_name)
        macro = evaluated[evaluated["label"].eq("macro")].iloc[0]
        rows.append(
            {
                "split": split,
                "threshold_mode": mode,
                "macro_auroc": float(macro["auroc"]),
                "macro_average_precision": float(macro["average_precision"]),
                "macro_f1": float(macro["f1"]),
                "micro_f1": float(macro["micro_f1"]),
            }
        )
    return pd.DataFrame(rows)


def _apply_output_override(config: dict[str, Any], root: Path, output_dir_override: str | Path | None) -> dict[str, Any]:
    if output_dir_override is None:
        return config
    out_dir = Path(output_dir_override)
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    cfg = copy.deepcopy(config)
    prefix = str(cfg.get("model", {}).get("name", "ablation_mlp"))
    cfg["output"] = {
        "val_predictions_csv": str(out_dir / f"{prefix}_val_predictions.csv"),
        "test_predictions_csv": str(out_dir / f"{prefix}_test_predictions.csv"),
        "history_csv": str(out_dir / f"{prefix}_training_history.csv"),
        "metrics_val_csv": str(out_dir / f"{prefix}_metrics_val.csv"),
        "metrics_test_csv": str(out_dir / f"{prefix}_metrics_test.csv"),
        "thresholds_json": str(out_dir / f"{prefix}_thresholds.json"),
        "run_summary_json": str(out_dir / f"{prefix}_run_summary.json"),
        "checkpoint_path": str(out_dir / f"{prefix}_best.pt"),
        "table_csv": str(out_dir / f"table_{prefix}_results.csv"),
        "threshold_comparison_csv": str(out_dir / f"table_{prefix}_threshold_comparison.csv"),
    }
    return cfg


def train(config_path: str | Path, seed_override: int | None = None, output_dir_override: str | Path | None = None) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    if seed_override is not None:
        config = copy.deepcopy(config)
        config.setdefault("training", {})["seed"] = int(seed_override)
    config = _apply_output_override(config, root, output_dir_override)
    paths = _paths(config, root)
    for key in ["train_csv", "val_csv", "test_csv"]:
        if paths[key] is None or not paths[key].exists():
            raise FileNotFoundError(f"Required fair fusion path missing: {key}={paths[key]}")

    labels = list(config.get("data", {}).get("labels", ["NORM", "MI", "STTC", "CD", "HYP"]))
    modality = str(config.get("model", {}).get("modality"))
    model_name = str(config.get("model", {}).get("name", f"{modality}_mlp"))
    training = config.get("training", {})
    model_cfg = config.get("model", {})
    seed = int(training.get("seed", 2026))
    _seed_everything(seed)
    device = _auto_device(str(training.get("device", "auto")))

    expected_structured_dim = int(model_cfg.get("expected_structured_dim", 531))
    train_ds = AblationDataset(paths["train_csv"], labels, modality, expected_structured_dim=expected_structured_dim)
    val_ds = AblationDataset(paths["val_csv"], labels, modality, expected_structured_dim=expected_structured_dim)
    test_ds = AblationDataset(paths["test_csv"], labels, modality, expected_structured_dim=expected_structured_dim)
    train_loader = _loader(train_ds, int(training.get("batch_size", 128)), True)
    val_loader = _loader(val_ds, int(training.get("batch_size", 128)), False)
    test_loader = _loader(test_ds, int(training.get("batch_size", 128)), False)

    model = FusionMLP(input_dim=len(train_ds.feature_cols), hidden_dims=model_cfg.get("hidden_dims", [256, 128]), num_classes=len(labels), dropout=float(model_cfg.get("dropout", 0.3))).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(training.get("learning_rate", 1e-3)), weight_decay=float(training.get("weight_decay", 1e-4)))
    epochs = int(training.get("epochs", 100))
    patience = int(training.get("patience", 10))
    min_delta = float(training.get("min_delta", 0.0005))
    best_score = -float("inf")
    best_epoch = 0
    best_state = None
    stale = 0
    history_rows = []
    for epoch in range(1, epochs + 1):
        loss = _run_epoch(model, train_loader, criterion, optimizer, device)
        y_val, p_val, _ = _predict(model, val_ds, val_loader, device, labels)
        val_eval = evaluate_multilabel_predictions(y_val, p_val, label_names=labels, split_name="val", model_name=model_name)
        macro = val_eval[val_eval["label"].eq("macro")].iloc[0]
        score = float(macro["auroc"])
        history_rows.append({"epoch": epoch, "train_loss": loss, "val_macro_auroc": score, "val_macro_f1": float(macro["f1"])})
        print(f"epoch={epoch} train_loss={loss:.6f} val_macro_auroc={score:.6f}")
        if score > best_score + min_delta:
            best_score = score
            best_epoch = epoch
            stale = 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            stale += 1
        if stale >= patience:
            print(f"early_stopping_epoch={epoch}")
            break
    if best_state is not None:
        model.load_state_dict(best_state)

    y_val, p_val, val_pred = _predict(model, val_ds, val_loader, device, labels)
    y_test, p_test, test_pred = _predict(model, test_ds, test_loader, device, labels)
    default_val = evaluate_multilabel_predictions(y_val, p_val, label_names=labels, split_name="val", model_name=model_name)
    default_test = evaluate_multilabel_predictions(y_test, p_test, label_names=labels, split_name="test", model_name=model_name)
    thresholds = tune_per_class_thresholds(y_val, p_val, label_names=labels)
    tuned_val = evaluate_multilabel_predictions(y_val, p_val, thresholds=thresholds, label_names=labels, split_name="val", model_name=model_name)
    tuned_test = evaluate_multilabel_predictions(y_test, p_test, thresholds=thresholds, label_names=labels, split_name="test", model_name=model_name)

    safe_to_csv(default_val, paths["metrics_val_csv"])
    safe_to_csv(default_test, paths["metrics_test_csv"])
    safe_to_csv(val_pred, paths["val_predictions_csv"])
    safe_to_csv(test_pred, paths["test_predictions_csv"])
    safe_to_csv(pd.DataFrame(history_rows), paths["history_csv"])
    save_thresholds(thresholds, paths["thresholds_json"])
    comparison = pd.concat([_threshold_comparison(y_val, p_val, labels, "val", thresholds, model_name), _threshold_comparison(y_test, p_test, labels, "test", thresholds, model_name)], ignore_index=True)
    safe_to_csv(comparison, paths["threshold_comparison_csv"])

    rows = []
    for threshold_mode, frame in [("default_0.5", default_val), ("default_0.5", default_test), ("validation_tuned", tuned_val), ("validation_tuned", tuned_test)]:
        macro = frame[frame["label"].eq("macro")].iloc[0]
        rows.append(
            {
                "model": model_name,
                "split": macro["split"],
                "threshold_mode": threshold_mode,
                "auroc": float(macro["auroc"]),
                "average_precision": float(macro["average_precision"]),
                "f1": float(macro["f1"]),
                "micro_f1": float(macro["micro_f1"]),
                "positive_count": int(macro["positive_count"]),
            }
        )
    safe_to_csv(pd.DataFrame(rows), paths["table_csv"])
    ensure_dir(paths["checkpoint_path"].parent)
    torch.save({"model_state_dict": model.state_dict(), "config": config, "labels": labels, "input_dim": len(train_ds.feature_cols), "best_epoch": best_epoch, "best_validation_score": best_score}, paths["checkpoint_path"])
    summary = {
        "config_path": str(config_path),
        "seed": seed,
        "model": model_name,
        "modality": modality,
        "n_train": len(train_ds),
        "n_val": len(val_ds),
        "n_test": len(test_ds),
        "input_dim": len(train_ds.feature_cols),
        "best_epoch": best_epoch,
        "best_validation_score": best_score,
        "threshold_tuning_split": "val",
        "early_stopping_split": "val",
        "test_role": "frozen_final_evaluation_only",
        "checkpoint_path": str(paths["checkpoint_path"]),
    }
    ensure_dir(paths["run_summary_json"].parent)
    paths["run_summary_json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"{model_name} completed. best_epoch={best_epoch} val_macro_auroc={best_score:.6f}")
    print(f"Table: {paths['table_csv']}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Train fair-interface ablation MLP.")
    parser.add_argument("--config")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    raise SystemExit(train(args.config, seed_override=args.seed, output_dir_override=args.output_dir))


if __name__ == "__main__":
    main()
