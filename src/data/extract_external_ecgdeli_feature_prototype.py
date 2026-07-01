from __future__ import annotations

import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import wfdb
from scipy.io import loadmat, savemat

from src.data.run_ecgdeli_smoke import _matlab_escape, _matlab_path_prefix
from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


DATASETS = ["cpsc2018", "chapman"]
N_RECORDS_PER_DATASET = 2
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]


def _matlab_script(cfg: dict[str, Any], signal_mat: Path, output_mat: Path) -> str:
    ecgdeli_dir = Path(cfg["repositories"]["ecgdeli_matlab"]).resolve()
    return "\n".join(
        [
            "try",
            _matlab_path_prefix(cfg),
            f"addpath(genpath('{_matlab_escape(ecgdeli_dir)}'));",
            f"load('{_matlab_escape(signal_mat)}');",
            "[ecg_filtered_frq] = ECG_High_Low_Filter(signal, Fs, 1, 40);",
            "ecg_filtered_frq = Notch_Filter(ecg_filtered_frq, Fs, 50, 1);",
            "[ecg_filtered_isoline, ~, ~, ~] = Isoline_Correction(ecg_filtered_frq);",
            "[FPT_MultiChannel, FPT_Cell] = Annotate_ECG_Multi(ecg_filtered_isoline, Fs);",
            "[Amplitude_feature_12leads] = ExtractAmplitudeFeaturesFromFPT(FPT_Cell, ecg_filtered_isoline);",
            "[Timing_feature_12leads, Timing_feature_sync] = ExtractIntervalFeaturesFromFPT(FPT_Cell, FPT_MultiChannel);",
            f"save('{_matlab_escape(output_mat)}', 'FPT_MultiChannel', 'Amplitude_feature_12leads', 'Timing_feature_12leads', 'Timing_feature_sync');",
            "fprintf('PROTOTYPE_STATUS=passed\\n');",
            "catch ME",
            "fprintf('PROTOTYPE_STATUS=failed\\n');",
            "fprintf('ERROR_IDENTIFIER=%s\\n', ME.identifier);",
            "fprintf('ERROR_MESSAGE=%s\\n', regexprep(ME.message, '\\n', ' '));",
            "exit(1);",
            "end",
        ]
    )


def _summaries(values: np.ndarray, prefix: str) -> dict[str, float]:
    flat = np.asarray(values, dtype=float).reshape(-1)
    finite = flat[np.isfinite(flat)]
    if finite.size == 0:
        return {f"{prefix}_mean": np.nan, f"{prefix}_iqr": np.nan, f"{prefix}_count": 0.0}
    return {
        f"{prefix}_mean": float(np.nanmean(finite)),
        f"{prefix}_iqr": float(np.nanpercentile(finite, 75) - np.nanpercentile(finite, 25)),
        f"{prefix}_count": float(finite.size),
    }


def _aggregate_features(mat_path: Path) -> dict[str, float]:
    mat = loadmat(mat_path)
    features: dict[str, float] = {}
    amplitude = np.asarray(mat["Amplitude_feature_12leads"], dtype=float)
    timing = np.asarray(mat["Timing_feature_12leads"], dtype=float)
    timing_sync = np.asarray(mat["Timing_feature_sync"], dtype=float)
    for lead_idx, lead in enumerate(LEADS):
        if lead_idx < amplitude.shape[0]:
            for feature_idx in range(amplitude.shape[2]):
                prefix = f"ecgdeli_proto_amp_f{feature_idx + 1}_{lead}"
                features.update(_summaries(amplitude[lead_idx, :, feature_idx], prefix))
        if lead_idx < timing.shape[0]:
            for feature_idx in range(timing.shape[2]):
                prefix = f"ecgdeli_proto_timing_f{feature_idx + 1}_{lead}"
                features.update(_summaries(timing[lead_idx, :, feature_idx], prefix))
    for feature_idx in range(timing_sync.shape[1]):
        prefix = f"ecgdeli_proto_timing_sync_f{feature_idx + 1}"
        features.update(_summaries(timing_sync[:, feature_idx], prefix))
    return features


def _load_signal(record_base: str) -> tuple[np.ndarray, float]:
    signal, fields = wfdb.rdsamp(record_base)
    fs = float(fields.get("fs", 500.0))
    if signal.ndim != 2:
        raise ValueError(f"Expected 2D ECG signal, got shape={signal.shape}")
    if signal.shape[1] != 12:
        raise ValueError(f"Expected 12 leads, got shape={signal.shape}")
    return np.asarray(signal, dtype=np.float64), fs


def _extract_one(cfg: dict[str, Any], row: pd.Series) -> tuple[dict[str, Any], dict[str, Any]]:
    record_id = str(row["record_id"])
    dataset = str(row["source_dataset"])
    record_base = str(row["record_base"])
    audit: dict[str, Any] = {
        "dataset": dataset,
        "record_id": record_id,
        "record_base": record_base,
        "status": "failed",
        "n_feature_columns": 0,
        "schema_exact_match": False,
        "blocking_issue": "ptbxl_plus_exact_531_recipe_missing",
        "notes": "",
    }
    base_features: dict[str, Any] = {"record_id": record_id, "source_dataset": dataset}
    with tempfile.TemporaryDirectory(prefix=f"ecgdeli_proto_{dataset}_{record_id}_") as tmp:
        tmpdir = Path(tmp)
        signal_mat = tmpdir / "input_signal.mat"
        output_mat = tmpdir / "ecgdeli_output.mat"
        script_path = tmpdir / "run_external_ecgdeli_prototype.m"
        signal, fs = _load_signal(record_base)
        savemat(signal_mat, {"signal": signal, "Fs": fs})
        script_path.write_text(_matlab_script(cfg, signal_mat, output_mat), encoding="utf-8")
        matlab = str(cfg.get("runtime_requirements", {}).get("matlab_executable", "") or "")
        proc = subprocess.run(
            [matlab, "-batch", f"run('{_matlab_escape(script_path)}')"],
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if proc.returncode != 0 or not output_mat.exists():
            audit["notes"] = (proc.stdout + "\n" + proc.stderr).replace("\n", " ")[:1000]
            return base_features, audit
        extracted = _aggregate_features(output_mat)
        base_features.update(extracted)
        audit.update(
            {
                "status": "generated_exploratory_features",
                "n_feature_columns": len(extracted),
                "notes": "Exploratory ECGdeli aggregation only; not frozen PTB-XL+ 531 schema.",
            }
        )
        return base_features, audit


def extract() -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    cfg = load_yaml("configs/ecgdeli_pipeline.yaml")
    out_dir = ensure_dir("data/processed/external")
    feature_tables: dict[str, pd.DataFrame] = {}
    audit_rows: list[dict[str, Any]] = []
    for dataset in DATASETS:
        manifest = pd.read_csv(out_dir / f"{dataset}_waveform_manifest.csv")
        sample = manifest[manifest["include_in_main_external_validation"].astype(bool)].head(N_RECORDS_PER_DATASET)
        rows: list[dict[str, Any]] = []
        for _, row in sample.iterrows():
            features, audit = _extract_one(cfg, row)
            rows.append(features)
            audit_rows.append(audit)
        table = pd.DataFrame(rows)
        feature_tables[dataset] = table
        safe_to_csv(table, out_dir / f"{dataset}_ecgdeli_features_prototype.csv")
    audit_df = pd.DataFrame(audit_rows)
    required = [line.strip() for line in Path("data/processed/structured_feature_names.txt").read_text().splitlines() if line.strip()]
    for dataset, table in feature_tables.items():
        cols = set(map(str, table.columns)) - {"record_id", "source_dataset"}
        matched = len(cols & set(required))
        audit_df.loc[audit_df["dataset"].eq(dataset), "matched_required_features"] = matched
        audit_df.loc[audit_df["dataset"].eq(dataset), "required_feature_count"] = len(required)
    return feature_tables, audit_df


def _write_summary(feature_tables: dict[str, pd.DataFrame], audit: pd.DataFrame) -> None:
    rows = []
    for dataset, table in feature_tables.items():
        rows.append(
            {
                "dataset": dataset,
                "n_rows": len(table),
                "n_columns": len(table.columns),
                "n_feature_columns": max(0, len(table.columns) - 2),
                "output": f"data/processed/external/{dataset}_ecgdeli_features_prototype.csv",
                "schema_exact_match": False,
            }
        )
    overview = pd.DataFrame(rows)
    text = "\n".join(
        [
            "# Stage 14E External ECGdeli Feature Prototype Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "A small ECGdeli-based external feature extraction prototype was run on two main-analysis records per external dataset. This stage verifies that external WFDB records can be passed through ECGdeli and summarized, but it does not reproduce the frozen PTB-XL+ 531-column feature schema.",
            "",
            "## Outputs",
            "",
            overview.to_markdown(index=False),
            "",
            "## Audit",
            "",
            audit.to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- The generated files are exploratory prototype features and use `ecgdeli_proto_*` column names.",
            "- They must not be used as fair concat or gated-fusion external inputs.",
            "- The remaining blocker is the missing exact PTB-XL+ ECGdeli 531-feature aggregation recipe.",
            "",
            "## Next Step",
            "",
            "Map the PTB-XL+ frozen feature names to ECGdeli amplitude, interval, morphology, and summary-statistic definitions, or obtain the official aggregation recipe. Only after schema validation passes should multimodal external validation be run.",
        ]
    )
    write_markdown("results/stage14e_external_ecgdeli_feature_prototype_summary.md", text + "\n")


def main() -> None:
    ensure_dir("results")
    ensure_dir("tables")
    feature_tables, audit = extract()
    safe_to_csv(audit, "tables/table_external_ecgdeli_feature_prototype_audit.csv")
    _write_summary(feature_tables, audit)
    print("Wrote external ECGdeli feature prototype outputs.")


if __name__ == "__main__":
    main()
