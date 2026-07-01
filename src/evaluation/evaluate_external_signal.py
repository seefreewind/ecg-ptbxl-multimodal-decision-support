from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import wfdb
from scipy.signal import resample_poly
from torch.utils.data import Dataset

from src.evaluation.evaluator import evaluate_multilabel_predictions
from src.models.signal_resnet import SignalResNet
from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
STANDARD_LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
TARGET_FS = 100
TARGET_LENGTH = 1000
MAIN_LABELS = {
    "cpsc2018": ["NORM", "CD"],
    "chapman": ["MI", "CD", "HYP"],
}
SNOMED_TO_LABEL = {
    "426783006": "NORM",  # CPSC2018 official normal/sinus rhythm class; Chapman SR is kept out of main NORM.
    "164865005": "MI",
    "270492004": "CD",
    "195042002": "CD",
    "54016002": "CD",
    "28189009": "CD",
    "27885002": "CD",
    "233917008": "CD",
    "698252002": "CD",
    "164909002": "CD",
    "59118001": "CD",
    "164873001": "HYP",
    "89792004": "HYP",
}


def _parse_header(path: Path) -> dict[str, Any]:
    lines = path.read_text(errors="ignore").splitlines()
    first = lines[0].split()
    if len(first) < 4:
        raise ValueError("WFDB header first line has fewer than four fields")
    fs = float(first[2].split("/")[0])
    if "/" in first[3]:
        raise ValueError("WFDB header does not expose signal length on the first line")
    length = int(float(first[3]))
    leads = []
    dx_codes: list[str] = []
    for line in lines[1:]:
        if line.startswith("#"):
            if line.lower().startswith("# dx:") or line.lower().startswith("#dx:"):
                dx_codes.extend([item.strip() for item in line.split(":", 1)[1].split(",") if item.strip()])
            continue
        parts = line.split()
        if len(parts) >= 9:
            leads.append(parts[-1])
    return {"record_id": path.stem, "fs": fs, "length": length, "duration": length / fs, "leads": leads, "dx_codes": dx_codes}


def _records_for_dataset(dataset: str, root: Path) -> pd.DataFrame:
    rows = []
    for hea in sorted(root.rglob("*.hea")):
        try:
            info = _parse_header(hea)
        except Exception:
            continue
        mapped = {label: 0 for label in LABELS}
        for code in info["dx_codes"]:
            label = SNOMED_TO_LABEL.get(str(code))
            if label:
                mapped[label] = 1
        row = {
            "record_id": info["record_id"],
            "source_dataset": dataset,
            "record_base": str(hea.with_suffix("")),
            "waveform_path": str(hea),
            "sampling_rate_original": info["fs"],
            "sampling_rate_target": TARGET_FS,
            "duration_original": info["duration"],
            "target_length": TARGET_LENGTH,
            "lead_order": ",".join(info["leads"]),
            "dx_codes": ",".join(info["dx_codes"]),
        }
        for label in LABELS:
            row[f"mapped_{label}"] = mapped[label]
        row["include_in_main_external_validation"] = any(mapped[label] for label in MAIN_LABELS[dataset])
        row["include_in_sensitivity_analysis"] = bool(mapped["STTC"] or (dataset == "chapman" and mapped["NORM"]))
        row["mapping_notes"] = "Actual SNOMED header mapping; main labels are pre-specified high-confidence subset."
        rows.append(row)
    return pd.DataFrame(rows)


def build_external_indices() -> dict[str, pd.DataFrame]:
    cfg = load_yaml("configs/data_external.yaml")
    out: dict[str, pd.DataFrame] = {}
    for dataset in ["cpsc2018", "chapman"]:
        root = Path(cfg["external"][dataset]["root_dir"])
        df = _records_for_dataset(dataset, root)
        out[dataset] = df
        stem = Path("data/processed/external") / dataset
        safe_to_csv(df, f"{stem}_index.csv")
        safe_to_csv(df, f"{stem}_labels_mapped.csv")
        safe_to_csv(df, f"{stem}_waveform_manifest.csv")
    return out


class ExternalSignalDataset(Dataset):
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.reset_index(drop=True)

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, dict[str, Any]]:
        row = self.df.iloc[idx]
        signal, fields = wfdb.rdsamp(str(row["record_base"]))
        x = np.asarray(signal, dtype=np.float32)
        lead_names = list(fields.get("sig_name", []))
        if lead_names:
            lead_index = {lead: i for i, lead in enumerate(lead_names)}
            x = np.stack([x[:, lead_index[lead]] for lead in STANDARD_LEADS], axis=1)
        fs = int(round(float(fields.get("fs", row["sampling_rate_original"]))))
        if fs != TARGET_FS:
            x = resample_poly(x, TARGET_FS, fs, axis=0).astype(np.float32)
        if x.shape[0] > TARGET_LENGTH:
            start = (x.shape[0] - TARGET_LENGTH) // 2
            x = x[start : start + TARGET_LENGTH]
        elif x.shape[0] < TARGET_LENGTH:
            pad = TARGET_LENGTH - x.shape[0]
            before = pad // 2
            after = pad - before
            x = np.pad(x, ((before, after), (0, 0)), mode="constant")
        x = x.T
        mean = x.mean(axis=1, keepdims=True)
        std = x.std(axis=1, keepdims=True)
        x = (x - mean) / np.maximum(std, 1e-6)
        meta = {"record_id": row["record_id"], "source_dataset": row["source_dataset"]}
        return torch.from_numpy(x.astype(np.float32)), meta


def _auto_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _load_model(device: torch.device) -> tuple[SignalResNet, list[str]]:
    checkpoint = torch.load("results/internal/signal_strong/signal_strong_best.pt", map_location=device)
    cfg = checkpoint["config"]
    model_cfg = cfg.get("model", {})
    labels = list(checkpoint.get("labels", LABELS))
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
        raise RuntimeError(f"Signal checkpoint load mismatch: missing={sorted(true_missing)} unexpected={unexpected}")
    model.to(device)
    model.eval()
    return model, labels


def _load_thresholds() -> dict[str, float]:
    return json.loads(Path("results/internal/signal_strong/val_tuned_thresholds.json").read_text())


def _load_temperatures(labels: list[str]) -> np.ndarray:
    path = Path("results/calibration/temperature_params_signal_strong.json")
    if not path.exists():
        return np.ones(len(labels), dtype=np.float32)
    params = json.loads(path.read_text())
    temps = np.asarray(params.get("temperatures", [1.0] * len(labels)), dtype=np.float32)
    return temps


@torch.no_grad()
def predict_dataset(dataset: str, df: pd.DataFrame, batch_size: int = 512) -> pd.DataFrame:
    device = _auto_device()
    model, labels = _load_model(device)
    temps = torch.from_numpy(_load_temperatures(labels)).to(device).view(1, -1)
    ds = ExternalSignalDataset(df)
    rows = []
    skipped = []
    batch_x: list[torch.Tensor] = []
    batch_meta: list[dict[str, Any]] = []

    def flush() -> None:
        if not batch_x:
            return
        x = torch.stack(batch_x).to(device)
        logits = model(x)
        probs = torch.sigmoid(logits / temps).cpu().numpy()
        raw_logits = logits.cpu().numpy()
        for i, meta in enumerate(batch_meta):
            row = {"record_id": meta["record_id"], "source_dataset": dataset, "model_name": "strong_signal_only", "probability_mode": "temperature_scaled"}
            for j, label in enumerate(labels):
                row[f"{label}_logit"] = float(raw_logits[i, j])
                row[f"{label}_prob"] = float(probs[i, j])
            rows.append(row)
        batch_x.clear()
        batch_meta.clear()

    for idx in range(len(ds)):
        try:
            x, meta = ds[idx]
        except Exception as exc:
            source_row = df.iloc[idx]
            skipped.append({"dataset": dataset, "record_id": source_row.get("record_id", ""), "record_base": source_row.get("record_base", ""), "error": str(exc)})
            continue
        batch_x.append(x)
        batch_meta.append(meta)
        if len(batch_x) >= batch_size:
            flush()
        if (idx + 1) % 5000 == 0:
            print(f"{dataset}: processed {idx + 1}/{len(ds)} records; predictions={len(rows)} skipped={len(skipped)}", flush=True)
    flush()
    if skipped:
        safe_to_csv(pd.DataFrame(skipped), f"results/external/{dataset}_signal_skipped_records.csv")
    else:
        safe_to_csv(pd.DataFrame(columns=["dataset", "record_id", "record_base", "error"]), f"results/external/{dataset}_signal_skipped_records.csv")
    return pd.DataFrame(rows)


def _metrics_for_dataset(dataset: str, labels_df: pd.DataFrame, pred: pd.DataFrame) -> pd.DataFrame:
    labels = MAIN_LABELS[dataset]
    merged = labels_df.merge(pred, on=["record_id", "source_dataset"], how="inner")
    y_true = merged[[f"mapped_{label}" for label in labels]].to_numpy(dtype=int)
    y_prob = merged[[f"{label}_prob" for label in labels]].to_numpy(dtype=float)
    thresholds_all = _load_thresholds()
    thresholds = {label: thresholds_all[label] for label in labels}
    metrics = evaluate_multilabel_predictions(
        y_true,
        y_prob,
        thresholds=thresholds,
        label_names=labels,
        split_name=f"external_{dataset}",
        model_name="strong_signal_only",
    )
    metrics.insert(0, "dataset", dataset)
    metrics["n_records"] = len(merged)
    metrics["threshold_source"] = "ptbxl_validation"
    metrics["temperature_source"] = "ptbxl_validation"
    metrics["external_label_scope"] = "high_confidence_subset"
    return metrics


def _write_summary(metrics: pd.DataFrame, indices: dict[str, pd.DataFrame]) -> None:
    macro = metrics[metrics["label"].eq("macro")][["dataset", "auroc", "average_precision", "f1", "positive_count", "n_records"]]
    coverage_rows = []
    for dataset, df in indices.items():
        labels = MAIN_LABELS[dataset]
        coverage_rows.append(
            {
                "dataset": dataset,
                "main_labels": "/".join(labels),
                "n_records": len(df),
                "positive_counts": "; ".join(f"{label}={int(df[f'mapped_{label}'].sum())}" for label in labels),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    text = "\n".join(
        [
            "# Stage 13B Signal-Only External Validation Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Scope",
            "",
            "This stage evaluates the frozen PTB-XL-trained `strong_signal_only` model on external datasets. No external training, fine-tuning, threshold tuning, or model selection was performed.",
            "",
            "Full multimodal external validation was not run because PTB-XL+ compatible structured features are not available for the external datasets.",
            "",
            "## Label Scope",
            "",
            coverage.to_markdown(index=False),
            "",
            "CPSC2018 uses the high-confidence NORM/CD subset. Chapman-Shaoxing uses the high-confidence MI/CD/HYP subset; sinus rhythm is not treated as main-analysis NORM.",
            "",
            "## Macro Metrics",
            "",
            macro.to_markdown(index=False),
            "",
            "## Interpretation Boundary",
            "",
            "- These are signal-only external results, not multimodal external validation.",
            "- These results do not establish clinical readiness.",
            "- Dataset label spaces are only partially aligned with the PTB-XL five-superclass task.",
            "",
            "## Next Step",
            "",
            "Use these results as conservative signal-only external evidence, or extract PTB-XL+ compatible structured features before any multimodal external validation.",
        ]
    )
    write_markdown("results/stage13b_signal_external_validation_summary.md", text + "\n")


def main() -> None:
    ensure_dir("results/external")
    ensure_dir("tables")
    indices = build_external_indices()
    metric_frames = []
    for dataset, df in indices.items():
        pred = predict_dataset(dataset, df)
        safe_to_csv(pred, f"results/external/{dataset}_signal_predictions.csv")
        metric_frames.append(_metrics_for_dataset(dataset, df, pred))
    metrics = pd.concat(metric_frames, ignore_index=True)
    safe_to_csv(metrics, "results/external/external_signal_metrics.csv")
    safe_to_csv(metrics, "tables/table_external_signal_results.csv")
    _write_summary(metrics, indices)
    print("Wrote signal-only external validation predictions, metrics, and summary.")


if __name__ == "__main__":
    main()
