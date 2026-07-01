from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


WAVEFORM_SUFFIXES = {".mat", ".hea", ".dat", ".npy", ".npz"}
STANDARD_12_LEADS = {"i", "ii", "iii", "avr", "avl", "avf", "v1", "v2", "v3", "v4", "v5", "v6"}
COMPAT_COLUMNS = [
    "dataset",
    "n_records_checked",
    "lead_count",
    "lead_order_detected",
    "sampling_rate_detected",
    "duration_detected",
    "target_sampling_rate",
    "target_length",
    "requires_resampling",
    "requires_padding_or_cropping",
    "compatible_with_signal_model",
    "blocking_issue",
    "notes",
]
STRUCTURED_COLUMNS = [
    "dataset",
    "has_external_structured_features",
    "feature_source",
    "n_features",
    "matches_ptbxl_plus_features",
    "missing_required_features",
    "can_run_signal_only",
    "can_run_fair_concat",
    "can_run_gated_fusion",
    "requires_feature_extraction",
    "recommended_external_validation_mode",
    "blocking_issue",
]


def _load_config() -> dict[str, Any]:
    return load_yaml("configs/data_external.yaml") if Path("configs/data_external.yaml").exists() else {}


def _dataset_root(dataset: str, candidates: pd.DataFrame, cfg: dict[str, Any]) -> Path:
    if not candidates.empty:
        row = candidates[candidates["dataset_candidate"].eq(dataset)]
        if not row.empty:
            return Path(str(row.iloc[0]["root_path"]))
    return Path(str(cfg.get("external", {}).get(dataset, {}).get("root_dir", f"data/raw/external/{dataset}")))


def _parse_header(path: Path) -> dict[str, Any]:
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except Exception:
        return {}
    if not lines:
        return {}
    first = lines[0].split()
    out: dict[str, Any] = {"lead_order": []}
    if len(first) >= 4:
        try:
            out["lead_count"] = int(first[1])
            out["sampling_rate"] = float(str(first[2]).split("/")[0])
            out["length"] = int(float(first[3]))
        except ValueError:
            pass
    leads = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 9:
            leads.append(parts[-1])
    if leads:
        out["lead_order"] = leads
        out["lead_count"] = out.get("lead_count", len(leads))
    if out.get("sampling_rate") and out.get("length"):
        out["duration"] = float(out["length"]) / float(out["sampling_rate"])
    return out


def _inspect_array_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".npy":
            arr = np.load(path, mmap_mode="r")
            shape = tuple(arr.shape)
        elif suffix == ".npz":
            data = np.load(path)
            first = data.files[0]
            shape = tuple(data[first].shape)
        else:
            return {}
    except Exception:
        return {}
    if len(shape) < 2:
        return {"shape": str(shape)}
    lead_count = min(shape[0], shape[-1]) if 12 in {shape[0], shape[-1]} else shape[0]
    length = max(shape[0], shape[-1])
    return {"lead_count": int(lead_count), "length": int(length), "shape": str(shape)}


def _inspect_dataset(dataset: str, root: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    dataset_cfg = cfg.get("external", {}).get(dataset, {})
    target_fs = int(dataset_cfg.get("target_sampling_rate", 100))
    target_seconds = int(dataset_cfg.get("target_duration_seconds", 10))
    target_length = target_fs * target_seconds
    if not root.exists():
        return {
            "dataset": dataset,
            "n_records_checked": 0,
            "lead_count": "",
            "lead_order_detected": "",
            "sampling_rate_detected": "",
            "duration_detected": "",
            "target_sampling_rate": target_fs,
            "target_length": target_length,
            "requires_resampling": False,
            "requires_padding_or_cropping": False,
            "compatible_with_signal_model": False,
            "blocking_issue": "external_raw_data_missing",
            "notes": "Place external raw data before compatibility can be confirmed.",
        }
    waveform_files = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in WAVEFORM_SUFFIXES]
    inspected = []
    for path in waveform_files[:20]:
        if path.suffix.lower() == ".hea":
            info = _parse_header(path)
        else:
            info = _inspect_array_file(path)
        if info:
            inspected.append(info)
    lead_counts = [int(item["lead_count"]) for item in inspected if item.get("lead_count")]
    sampling_rates = [float(item["sampling_rate"]) for item in inspected if item.get("sampling_rate")]
    durations = [float(item["duration"]) for item in inspected if item.get("duration")]
    lead_orders = [item.get("lead_order", []) for item in inspected if item.get("lead_order")]
    lead_count = int(pd.Series(lead_counts).mode().iloc[0]) if lead_counts else ""
    sampling_rate = float(pd.Series(sampling_rates).mode().iloc[0]) if sampling_rates else ""
    duration = float(np.median(durations)) if durations else ""
    lead_order = lead_orders[0] if lead_orders else []
    lead_set = {str(lead).lower() for lead in lead_order}
    lead_order_ok = bool(lead_set) and STANDARD_12_LEADS.issubset(lead_set)
    lead_count_ok = lead_count == 12
    requires_resampling = bool(sampling_rate) and not np.isclose(float(sampling_rate), target_fs)
    requires_crop_pad = bool(duration) and not np.isclose(float(duration), target_seconds, atol=0.1)
    compatible = bool(lead_count_ok and (not lead_order or lead_order_ok) and (sampling_rate or duration or waveform_files))
    blocking = ""
    if not waveform_files:
        compatible = False
        blocking = "no_waveform_files_found"
    elif not lead_count_ok:
        compatible = False
        blocking = "lead_count_not_confirmed_as_12"
    elif lead_order and not lead_order_ok:
        compatible = False
        blocking = "lead_order_not_mappable_to_ptbxl_12_leads"
    elif not sampling_rate:
        blocking = "sampling_rate_unknown_manual_confirmation_required"
    elif not duration:
        blocking = "duration_unknown_manual_confirmation_required"
    return {
        "dataset": dataset,
        "n_records_checked": len(inspected),
        "lead_count": lead_count,
        "lead_order_detected": ",".join(map(str, lead_order)),
        "sampling_rate_detected": sampling_rate,
        "duration_detected": duration,
        "target_sampling_rate": target_fs,
        "target_length": target_length,
        "requires_resampling": requires_resampling,
        "requires_padding_or_cropping": requires_crop_pad,
        "compatible_with_signal_model": compatible,
        "blocking_issue": blocking,
        "notes": "Compatible after documented preprocessing." if compatible else "Not ready for external validation.",
    }


def _structured_feasibility(dataset: str, root: Path, waveform_row: dict[str, Any]) -> dict[str, Any]:
    required = []
    feature_names = Path("data/processed/structured_feature_names.txt")
    if feature_names.exists():
        required = [line.strip() for line in feature_names.read_text().splitlines() if line.strip()]
    feature_files = []
    if root.exists():
        feature_files = [
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".csv", ".tsv", ".parquet", ".feather", ".pkl", ".pickle"}
            and any(token in path.name.lower() for token in ["feature", "ecgdeli", "structured"])
        ]
    matched = False
    n_features = 0
    missing_required = len(required)
    feature_source = ""
    for path in feature_files[:10]:
        try:
            if path.suffix.lower() == ".csv":
                df = pd.read_csv(path, nrows=1)
            elif path.suffix.lower() == ".tsv":
                df = pd.read_csv(path, sep="\t", nrows=1)
            else:
                continue
        except Exception:
            continue
        cols = set(map(str, df.columns))
        present = sorted(set(required) & cols)
        if len(present) > n_features:
            n_features = len(present)
            missing_required = len(set(required) - cols)
            feature_source = str(path)
            matched = missing_required == 0 and len(required) > 0
    can_signal = bool(waveform_row.get("compatible_with_signal_model"))
    has_features = bool(feature_source)
    recommended = "not_ready"
    blocking = str(waveform_row.get("blocking_issue") or "")
    if can_signal and matched:
        recommended = "multimodal_full"
        blocking = ""
    elif can_signal and not has_features:
        recommended = "signal_only_main"
        blocking = "external_structured_features_missing_for_multimodal"
    elif can_signal and has_features and not matched:
        recommended = "external_feature_extraction_required"
        blocking = "external_structured_features_do_not_match_ptbxl_plus"
    return {
        "dataset": dataset,
        "has_external_structured_features": has_features,
        "feature_source": feature_source,
        "n_features": n_features,
        "matches_ptbxl_plus_features": matched,
        "missing_required_features": missing_required,
        "can_run_signal_only": can_signal,
        "can_run_fair_concat": matched,
        "can_run_gated_fusion": matched,
        "requires_feature_extraction": bool(can_signal and not matched),
        "recommended_external_validation_mode": recommended,
        "blocking_issue": blocking,
    }


def _write_reports(waveform: pd.DataFrame, structured: pd.DataFrame) -> None:
    write_markdown(
        "results/external/external_waveform_compatibility_report.md",
        "\n".join(
            [
                "# External Waveform Compatibility Report",
                "",
                "Generated date: " + date.today().isoformat(),
                "",
                waveform.to_markdown(index=False),
                "",
                "Target signal-model input shape: `12 channels x 1000 samples`.",
            ]
        )
        + "\n",
    )
    write_markdown(
        "results/external/external_multimodal_feasibility_report.md",
        "\n".join(
            [
                "# External Multimodal Feasibility Report",
                "",
                "Generated date: " + date.today().isoformat(),
                "",
                structured.to_markdown(index=False),
                "",
                "Full multimodal external validation is allowed only when PTB-XL+ structured features are matched or a pre-specified missing-modality pathway has been validated.",
            ]
        )
        + "\n",
    )


def main() -> None:
    ensure_dir("results/external")
    ensure_dir("tables")
    cfg = _load_config()
    candidates_path = Path("results/external/external_dataset_candidates.csv")
    candidates = pd.read_csv(candidates_path) if candidates_path.exists() else pd.DataFrame()
    waveform_rows = []
    structured_rows = []
    for dataset in ["cpsc2018", "chapman"]:
        root = _dataset_root(dataset, candidates, cfg)
        row = _inspect_dataset(dataset, root, cfg)
        waveform_rows.append(row)
        structured_rows.append(_structured_feasibility(dataset, root, row))
    waveform = pd.DataFrame(waveform_rows, columns=COMPAT_COLUMNS)
    structured = pd.DataFrame(structured_rows, columns=STRUCTURED_COLUMNS)
    safe_to_csv(waveform, "tables/table_external_waveform_compatibility.csv")
    safe_to_csv(structured, "tables/table_external_structured_feature_compatibility.csv")
    _write_reports(waveform, structured)
    print("Wrote external waveform compatibility and multimodal feasibility reports.")


if __name__ == "__main__":
    main()
