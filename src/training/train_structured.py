from __future__ import annotations

import argparse
import json
import pickle
import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression

from src.training.metrics import compute_multilabel_metrics
from src.utils.io import ensure_dir, load_yaml, project_root_from_config, resolve_path, safe_to_csv


def _paths(config: dict[str, Any], root: Path) -> dict[str, Path]:
    data = config.get("data", {})
    output = config.get("output", {})
    return {
        "features_csv": resolve_path(data.get("features_csv", "data/processed/ptbxl_structured_features.csv"), root),
        "index_csv": resolve_path(data.get("index_csv", "data/processed/ptbxl_multimodal_index.csv"), root),
        "feature_names_txt": resolve_path(data.get("feature_names_txt", "data/processed/structured_feature_names.txt"), root),
        "metrics_csv": resolve_path(output.get("metrics_csv", "results/internal/structured_baseline_metrics.csv"), root),
        "table_csv": resolve_path(output.get("table_csv", "tables/table_structured_baseline_results.csv"), root),
        "val_predictions_csv": resolve_path(output.get("val_predictions_csv", "results/internal/structured_val_predictions.csv"), root),
        "test_predictions_csv": resolve_path(output.get("test_predictions_csv", "results/internal/structured_test_predictions.csv"), root),
        "run_summary_json": resolve_path(output.get("run_summary_json", "results/internal/structured_run_summary.json"), root),
        "model_path": resolve_path(output.get("model_path", "results/internal/structured_logistic.pkl"), root),
    }


def _require_paths(paths: dict[str, Path]) -> None:
    for key in ["features_csv", "index_csv"]:
        path = paths[key]
        if path is None or not path.exists():
            raise FileNotFoundError(f"Required structured baseline path missing: {key}={path}")


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _read_feature_names(paths: dict[str, Path], features: pd.DataFrame) -> list[str]:
    names_path = paths.get("feature_names_txt")
    if names_path is not None and names_path.exists():
        names = [line.strip() for line in names_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        names = [name for name in names if name in features.columns and name != "ecg_id"]
        if names:
            return names
    return [col for col in features.columns if col != "ecg_id"]


def _load_dataset(paths: dict[str, Path], labels: list[str]) -> tuple[pd.DataFrame, list[str]]:
    features = pd.read_csv(paths["features_csv"])
    index = pd.read_csv(paths["index_csv"])
    required_index = ["ecg_id", "split"] + labels
    missing_index = [col for col in required_index if col not in index.columns]
    if missing_index:
        raise ValueError(f"{paths['index_csv']} is missing required columns: {missing_index}")
    if "ecg_id" not in features.columns:
        raise ValueError(f"{paths['features_csv']} is missing required column: ecg_id")

    feature_names = _read_feature_names(paths, features)
    if not feature_names:
        raise ValueError("No structured feature columns are available.")

    merged = index[required_index].merge(features[["ecg_id"] + feature_names], on="ecg_id", how="inner")
    if merged.empty:
        raise ValueError("No rows remain after joining structured features to PTB-XL labels.")
    return merged, feature_names


def _fit_models(
    x_train: np.ndarray,
    y_train: np.ndarray,
    labels: list[str],
    model_cfg: dict[str, Any],
) -> list[LogisticRegression | DummyClassifier]:
    models: list[LogisticRegression | DummyClassifier] = []
    for idx, label in enumerate(labels):
        y = y_train[:, idx].astype(int)
        if np.unique(y).size < 2:
            model = DummyClassifier(strategy="constant", constant=int(y[0]))
            model.fit(x_train, y)
        else:
            model = LogisticRegression(
                C=float(model_cfg.get("C", 1.0)),
                class_weight=model_cfg.get("class_weight", "balanced"),
                max_iter=int(model_cfg.get("max_iter", 500)),
                solver=str(model_cfg.get("solver", "liblinear")),
                random_state=int(model_cfg.get("random_state", 2026)),
            )
            model.fit(x_train, y)
        models.append(model)
    return models


def _predict_prob(models: list[LogisticRegression | DummyClassifier], x: np.ndarray) -> np.ndarray:
    probs: list[np.ndarray] = []
    for model in models:
        if isinstance(model, DummyClassifier):
            proba = model.predict_proba(x)
            cls = int(model.classes_[0])
            positive_prob = np.ones(x.shape[0], dtype=float) if cls == 1 else np.zeros(x.shape[0], dtype=float)
        else:
            classes = list(model.classes_)
            if classes == [0, 1]:
                logits = np.sum(x * model.coef_.reshape(1, -1), axis=1) + float(model.intercept_[0])
                logits = np.clip(logits, -500.0, 500.0)
                positive_prob = 1.0 / (1.0 + np.exp(-logits))
            else:
                proba = model.predict_proba(x)
                positive_idx = classes.index(1)
                positive_prob = proba[:, positive_idx]
        probs.append(positive_prob)
    return np.vstack(probs).T


def _prediction_frame(meta: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray, labels: list[str]) -> pd.DataFrame:
    out = meta.copy()
    for idx, label in enumerate(labels):
        out[f"{label}_true"] = y_true[:, idx].astype(int)
        out[f"{label}_prob"] = y_prob[:, idx]
    return out


def _split_xy(df: pd.DataFrame, split: str, labels: list[str], feature_names: list[str]) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    part = df[df["split"].eq(split)].copy()
    if part.empty:
        raise ValueError(f"No rows found for split={split}.")
    x = part[feature_names].replace([np.inf, -np.inf], np.nan).to_numpy(dtype=float)
    y = part[labels].to_numpy(dtype=np.float32)
    return part[["ecg_id", "split"]].reset_index(drop=True), x, y


def _fit_standardizer(x_train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(x_train, axis=0)
    std = np.std(x_train, axis=0)
    std = np.where(std < 1e-8, 1.0, std)
    return mean, std


def _apply_standardizer(x: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return (x - mean) / std


def train(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    paths = _paths(config, root)
    _require_paths(paths)

    labels = list(config.get("data", {}).get("labels", ["NORM", "MI", "STTC", "CD", "HYP"]))
    training = config.get("training", {})
    model_cfg = dict(config.get("model", {}))
    model_cfg.setdefault("random_state", int(training.get("seed", 2026)))
    _seed_everything(int(training.get("seed", 2026)))

    df, feature_names = _load_dataset(paths, labels)
    max_train_rows = training.get("max_train_rows")
    if max_train_rows not in {None, "null", "None", 0, "0"}:
        train_ids = df[df["split"].eq("train")]["ecg_id"].head(int(max_train_rows))
        df = pd.concat([df[~df["split"].eq("train")], df[df["ecg_id"].isin(train_ids)]], ignore_index=True)

    train_meta, x_train_raw, y_train = _split_xy(df, "train", labels, feature_names)
    val_meta, x_val_raw, y_val = _split_xy(df, "val", labels, feature_names)
    test_meta, x_test_raw, y_test = _split_xy(df, "test", labels, feature_names)

    imputer = SimpleImputer(strategy=str(training.get("imputation_strategy", "median")))
    x_train_imputed = imputer.fit_transform(x_train_raw)
    mean, std = _fit_standardizer(x_train_imputed)
    x_train = _apply_standardizer(x_train_imputed, mean, std)
    x_val = _apply_standardizer(imputer.transform(x_val_raw), mean, std)
    x_test = _apply_standardizer(imputer.transform(x_test_raw), mean, std)

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
                "feature_names": feature_names,
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
        "n_features": int(len(feature_names)),
        "model": str(config.get("model", {}).get("name", "structured_logistic")),
        "metrics_csv": str(paths["metrics_csv"]),
        "table_csv": str(paths["table_csv"]),
        "model_path": str(paths["model_path"]),
    }
    ensure_dir(paths["run_summary_json"].parent)
    paths["run_summary_json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Structured baseline completed.")
    print(f"Rows: train={len(train_meta)} val={len(val_meta)} test={len(test_meta)}")
    print(f"Features: {len(feature_names)}")
    print(f"Metrics: {paths['metrics_csv']}")
    print(f"Table: {paths['table_csv']}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PTB-XL+ structured-only baseline.")
    parser.add_argument("--config", default="configs/model_structured_logistic.yaml", help="Path to structured baseline config")
    args = parser.parse_args()
    raise SystemExit(train(args.config))


if __name__ == "__main__":
    main()
