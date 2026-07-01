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
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.evaluation.evaluator import evaluate_multilabel_predictions
from src.models.signal_resnet import SignalResNet
from src.training.metrics import compute_multilabel_metrics
from src.training.thresholds import save_thresholds, tune_per_class_thresholds
from src.utils.io import ensure_dir, load_yaml, project_root_from_config, resolve_path, safe_to_csv


class PTBXLSignalDataset(Dataset):
    def __init__(self, csv_path: Path, records_base_dir: Path, label_names: list[str]) -> None:
        self.df = pd.read_csv(csv_path)
        self.records_base_dir = records_base_dir
        self.label_names = label_names
        required = ["filename_lr"] + label_names
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            raise ValueError(f"{csv_path} is missing required columns: {missing}")

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        row = self.df.iloc[idx]
        record_base = self.records_base_dir / str(row["filename_lr"])
        signal, _ = wfdb.rdsamp(str(record_base))
        x = np.asarray(signal, dtype=np.float32).T
        mean = x.mean(axis=1, keepdims=True)
        std = x.std(axis=1, keepdims=True)
        x = (x - mean) / np.maximum(std, 1e-6)
        y = row[self.label_names].to_numpy(dtype=np.float32)
        return torch.from_numpy(x), torch.from_numpy(y)


def _paths(config: dict[str, Any], root: Path) -> dict[str, Path]:
    data = config.get("data", {})
    output = config.get("output", {})
    return {
        "train_csv": resolve_path(data.get("train_csv", "data/splits/ptbxl_train.csv"), root),
        "val_csv": resolve_path(data.get("val_csv", "data/splits/ptbxl_val.csv"), root),
        "test_csv": resolve_path(data.get("test_csv", "data/splits/ptbxl_test.csv"), root),
        "records_base_dir": resolve_path(data.get("records_base_dir", "data/raw/ptbxl"), root),
        "metrics_csv": resolve_path(output.get("metrics_csv", "results/internal/signal_baseline_metrics.csv"), root),
        "table_csv": resolve_path(output.get("table_csv", "tables/table_signal_baseline_results.csv"), root),
        "val_predictions_csv": resolve_path(output.get("val_predictions_csv", "results/internal/signal_val_predictions.csv"), root),
        "test_predictions_csv": resolve_path(output.get("test_predictions_csv", "results/internal/signal_test_predictions.csv"), root),
        "history_csv": resolve_path(output.get("history_csv", "results/internal/signal_training_history.csv"), root),
        "run_summary_json": resolve_path(output.get("run_summary_json", "results/internal/signal_run_summary.json"), root),
        "checkpoint_path": resolve_path(output.get("checkpoint_path", "results/internal/signal_resnet.pt"), root),
        "best_checkpoint_path": resolve_path(output.get("best_checkpoint_path", output.get("checkpoint_path", "results/internal/signal_resnet.pt")), root),
        "metrics_val_csv": resolve_path(output.get("metrics_val_csv"), root),
        "metrics_test_csv": resolve_path(output.get("metrics_test_csv"), root),
        "thresholds_json": resolve_path(output.get("thresholds_json"), root),
        "thresholds_table_csv": resolve_path(output.get("thresholds_table_csv"), root),
        "threshold_comparison_csv": resolve_path(output.get("threshold_comparison_csv"), root),
    }


def _require_paths(paths: dict[str, Path]) -> None:
    for key in ["train_csv", "val_csv", "test_csv", "records_base_dir"]:
        path = paths[key]
        if path is None or not path.exists():
            raise FileNotFoundError(f"Required signal baseline path missing: {key}={path}")


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


def _make_loader(dataset: Dataset, config: dict[str, Any], shuffle: bool) -> DataLoader:
    training = config.get("training", {})
    return DataLoader(
        dataset,
        batch_size=int(training.get("batch_size", 32)),
        shuffle=shuffle,
        num_workers=int(training.get("num_workers", 0)),
    )


def _run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    max_batches: int | None,
) -> float:
    model.train()
    losses: list[float] = []
    for batch_idx, (x, y) in enumerate(loader):
        if max_batches is not None and batch_idx >= max_batches:
            break
        x = x.to(device)
        y = y.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses)) if losses else float("nan")


def _normalise_batch_limit(value: Any) -> int | None:
    if value in {None, "null", "None", 0, "0"}:
        return None
    return int(value)


@torch.no_grad()
def _predict(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    max_batches: int | None,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    model.eval()
    ys: list[np.ndarray] = []
    ps: list[np.ndarray] = []
    meta_frames: list[pd.DataFrame] = []
    for batch_idx, (x, y) in enumerate(loader):
        if max_batches is not None and batch_idx >= max_batches:
            break
        logits = model(x.to(device))
        ys.append(y.numpy())
        ps.append(torch.sigmoid(logits).cpu().numpy())
        start = batch_idx * loader.batch_size
        end = start + len(y)
        dataset = loader.dataset
        if not isinstance(dataset, PTBXLSignalDataset):
            raise TypeError("Signal prediction loader must wrap PTBXLSignalDataset.")
        meta_frames.append(dataset.df.iloc[start:end][["ecg_id", "filename_lr"]].reset_index(drop=True))
    if not ys:
        raise ValueError("No batches were evaluated; check split files and max_eval_batches.")
    return np.concatenate(ys, axis=0), np.concatenate(ps, axis=0), pd.concat(meta_frames, ignore_index=True)


def _prediction_frame(meta: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray, labels: list[str]) -> pd.DataFrame:
    out = meta.copy()
    for idx, label in enumerate(labels):
        out[f"{label}_true"] = y_true[:, idx].astype(int)
        out[f"{label}_prob"] = y_prob[:, idx]
    return out


def _threshold_comparison(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    labels: list[str],
    split: str,
    tuned_thresholds: dict[str, float],
) -> pd.DataFrame:
    rows = []
    for mode, thresholds in [("default_0.5", None), ("validation_tuned", tuned_thresholds)]:
        evaluated = evaluate_multilabel_predictions(y_true, y_prob, thresholds=thresholds, label_names=labels, split_name=split)
        macro = evaluated[evaluated["label"].eq("macro")].iloc[0]
        row: dict[str, Any] = {
            "split": split,
            "threshold_mode": mode,
            "macro_auroc": float(macro["auroc"]),
            "macro_average_precision": float(macro["average_precision"]),
            "macro_f1": float(macro["f1"]),
            "micro_f1": float(macro["micro_f1"]),
        }
        for label in labels:
            label_row = evaluated[evaluated["label"].eq(label)].iloc[0]
            row[f"per_class_f1_{label}"] = float(label_row["f1"])
        rows.append(row)
    return pd.DataFrame(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def train(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    paths = _paths(config, root)
    _require_paths(paths)

    labels = list(config.get("data", {}).get("labels", ["NORM", "MI", "STTC", "CD", "HYP"]))
    training = config.get("training", {})
    model_cfg = config.get("model", {})
    _seed_everything(int(training.get("seed", 2026)))

    device = _auto_device(str(training.get("device", "cpu")))
    train_ds = PTBXLSignalDataset(paths["train_csv"], paths["records_base_dir"], labels)
    val_ds = PTBXLSignalDataset(paths["val_csv"], paths["records_base_dir"], labels)
    test_ds = PTBXLSignalDataset(paths["test_csv"], paths["records_base_dir"], labels)
    train_loader = _make_loader(train_ds, config, shuffle=not bool(training.get("dry_run", False)))
    val_loader = _make_loader(val_ds, config, shuffle=False)
    test_loader = _make_loader(test_ds, config, shuffle=False)

    model = SignalResNet(
        in_channels=int(model_cfg.get("input_channels", 12)),
        num_classes=int(model_cfg.get("num_classes", len(labels))),
        base_channels=int(model_cfg.get("base_channels", 32)),
        blocks_per_stage=tuple(model_cfg.get("blocks_per_stage", [2, 2, 2])),
        dropout=float(model_cfg.get("dropout", 0.1)),
    ).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(training.get("learning_rate", 1e-3)),
        weight_decay=float(training.get("weight_decay", 1e-4)),
    )

    max_train_batches = training.get("max_train_batches_per_epoch", training.get("max_train_batches"))
    max_eval_batches = training.get("max_eval_batches")
    if bool(training.get("dry_run", False)):
        max_train_batches = 1 if max_train_batches is None else int(max_train_batches)
        max_eval_batches = 1 if max_eval_batches is None else int(max_eval_batches)
    else:
        max_train_batches = _normalise_batch_limit(max_train_batches)
        max_eval_batches = _normalise_batch_limit(max_eval_batches)

    epochs = int(training.get("epochs", 1))
    patience = training.get("patience")
    patience = None if patience in {None, "null", "None"} else int(patience)
    min_delta = float(training.get("min_delta", 0.0))
    save_best_on = str(training.get("save_best_on", "val_macro_auroc"))
    best_score = -float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    best_state: dict[str, torch.Tensor] | None = None
    history_rows: list[dict[str, Any]] = []
    for epoch in range(epochs):
        loss = _run_epoch(model, train_loader, criterion, optimizer, device, max_train_batches)
        y_val, p_val, _ = _predict(model, val_loader, device, max_eval_batches)
        val_eval = evaluate_multilabel_predictions(y_val, p_val, label_names=labels, split_name="val", model_name=model_cfg.get("name", "signal_resnet"))
        val_macro = val_eval[val_eval["label"].eq("macro")].iloc[0]
        val_macro_auroc = float(val_macro["auroc"])
        history_rows.append({"epoch": epoch + 1, "train_loss": loss, "val_macro_auroc": val_macro_auroc, "val_macro_f1": float(val_macro["f1"])})
        print(f"epoch={epoch + 1} train_loss={loss:.6f} val_macro_auroc={val_macro_auroc:.6f}")
        current_score = val_macro_auroc if save_best_on == "val_macro_auroc" else float(val_macro["f1"])
        if current_score > best_score + min_delta:
            best_score = current_score
            best_epoch = epoch + 1
            epochs_without_improvement = 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            epochs_without_improvement += 1
        if patience is not None and epochs_without_improvement >= patience:
            print(f"early_stopping_epoch={epoch + 1}")
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    metric_frames = []
    prediction_outputs: dict[str, pd.DataFrame] = {}
    arrays: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for split, loader in [("val", val_loader), ("test", test_loader)]:
        y_true, y_prob, meta = _predict(model, loader, device, max_eval_batches)
        arrays[split] = (y_true, y_prob)
        metric_frames.append(compute_multilabel_metrics(y_true, y_prob, labels, split=split))
        prediction_outputs[split] = _prediction_frame(meta, y_true, y_prob, labels)
    metrics = pd.concat(metric_frames, ignore_index=True)
    safe_to_csv(metrics, paths["metrics_csv"])
    if paths.get("metrics_val_csv") is not None:
        safe_to_csv(metrics[metrics["split"].eq("val")], paths["metrics_val_csv"])
    if paths.get("metrics_test_csv") is not None:
        safe_to_csv(metrics[metrics["split"].eq("test")], paths["metrics_test_csv"])
    table = metrics[metrics["label"].eq("macro")].copy()
    safe_to_csv(table, paths["table_csv"])
    safe_to_csv(prediction_outputs["val"], paths["val_predictions_csv"])
    safe_to_csv(prediction_outputs["test"], paths["test_predictions_csv"])
    safe_to_csv(pd.DataFrame(history_rows), paths["history_csv"])
    ensure_dir(paths["checkpoint_path"].parent)
    checkpoint_payload = {
        "model_state_dict": model.state_dict(),
        "config": config,
        "labels": labels,
        "history": history_rows,
        "best_epoch": best_epoch,
        "best_validation_score": best_score,
    }
    torch.save(
        checkpoint_payload,
        paths["checkpoint_path"],
    )
    if paths["best_checkpoint_path"] != paths["checkpoint_path"]:
        ensure_dir(paths["best_checkpoint_path"].parent)
        torch.save(checkpoint_payload, paths["best_checkpoint_path"])

    evaluation = config.get("evaluation", {})
    tuned_thresholds: dict[str, float] | None = None
    if bool(evaluation.get("tune_thresholds_on_validation", False)):
        y_val, p_val = arrays["val"]
        tuned_thresholds = tune_per_class_thresholds(
            y_val,
            p_val,
            metric=str(evaluation.get("threshold_metric", "f1")).replace("macro_", ""),
            label_names=labels,
        )
        if paths.get("thresholds_json") is not None:
            save_thresholds(tuned_thresholds, paths["thresholds_json"])
        if paths.get("thresholds_table_csv") is not None:
            safe_to_csv(pd.DataFrame([{"label": label, "threshold": tuned_thresholds[label]} for label in labels]), paths["thresholds_table_csv"])
        if paths.get("threshold_comparison_csv") is not None:
            comparison = pd.concat(
                [
                    _threshold_comparison(*arrays["val"], labels=labels, split="val", tuned_thresholds=tuned_thresholds),
                    _threshold_comparison(*arrays["test"], labels=labels, split="test", tuned_thresholds=tuned_thresholds),
                ],
                ignore_index=True,
            )
            safe_to_csv(comparison, paths["threshold_comparison_csv"])

    _write_json(
        paths["run_summary_json"],
        {
            "config_path": str(config_path),
            "labels": labels,
            "n_train": len(train_ds),
            "n_val": len(val_ds),
            "n_test": len(test_ds),
            "epochs_requested": epochs,
            "epochs_completed": len(history_rows),
            "early_stopping_epoch": len(history_rows) if patience is not None and len(history_rows) < epochs else None,
            "best_epoch": best_epoch,
            "best_validation_score": best_score,
            "save_best_on": save_best_on,
            "dry_run": bool(training.get("dry_run", False)),
            "max_train_batches": max_train_batches,
            "max_eval_batches": max_eval_batches,
            "device": str(device),
            "metrics_csv": str(paths["metrics_csv"]),
            "table_csv": str(paths["table_csv"]),
            "checkpoint_path": str(paths["checkpoint_path"]),
            "best_checkpoint_path": str(paths["best_checkpoint_path"]),
            "thresholds_json": str(paths["thresholds_json"]) if paths.get("thresholds_json") else "",
        },
    )
    print(f"Metrics: {paths['metrics_csv']}")
    print(f"Table: {paths['table_csv']}")
    print(f"Checkpoint: {paths['checkpoint_path']}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Train minimal PTB-XL signal-only baseline.")
    parser.add_argument("--config", default="configs/model_signal_resnet.yaml", help="Path to signal model config")
    args = parser.parse_args()
    raise SystemExit(train(args.config))


if __name__ == "__main__":
    main()
