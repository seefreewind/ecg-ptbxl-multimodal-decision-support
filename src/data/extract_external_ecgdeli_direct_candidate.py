from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.io import loadmat

from src.data.extract_external_ecgdeli_feature_prototype import (
    DATASETS,
    LEADS,
    N_RECORDS_PER_DATASET,
    _extract_one,
)
from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


LEADWISE_INDEX = {
    "P_Amp": ("Amplitude_feature_12leads", 0),
    "Q_Amp": ("Amplitude_feature_12leads", 1),
    "R_Amp": ("Amplitude_feature_12leads", 2),
    "S_Amp": ("Amplitude_feature_12leads", 3),
    "T_Amp": ("Amplitude_feature_12leads", 4),
    "P_DurFull": ("Timing_feature_12leads", 0),
    "QRS_Dur": ("Timing_feature_12leads", 1),
    "T_DurFull": ("Timing_feature_12leads", 2),
    "PQ_Int": ("Timing_feature_12leads", 3),
    "PR_Int": ("Timing_feature_12leads", 4),
    "QT_Int": ("Timing_feature_12leads", 5),
}

GLOBAL_INDEX = {
    "P_Dur": 0,
    "QRS_Dur": 1,
    "T_Dur": 2,
    "PQ_Int": 3,
    "PR_Int": 4,
    "QT_Int": 5,
    "QT_IntFramingham": 6,
    "RR_Mean": 7,
}


def _summary_values(values: np.ndarray) -> dict[str, float]:
    flat = np.asarray(values, dtype=float).reshape(-1)
    finite = flat[np.isfinite(flat)]
    if finite.size == 0:
        return {"mean": np.nan, "iqr": np.nan, "count": 0.0}
    return {
        "mean": float(np.nanmean(finite)),
        "iqr": float(np.nanpercentile(finite, 75) - np.nanpercentile(finite, 25)),
        "count": float(finite.size),
    }


def _assign_stat(features: dict[str, Any], name: str, values: np.ndarray) -> None:
    stats = _summary_values(values)
    features[name] = stats["mean"]
    features[f"{name}_iqr"] = stats["iqr"]
    features[f"{name}_count"] = stats["count"]


def _direct_feature_names() -> list[str]:
    mapping = pd.read_csv("tables/table_ptbxl_plus_ecgdeli_feature_mapping_audit.csv")
    return list(mapping.loc[mapping["derivability"].eq("direct_ecgdeli"), "ptbxl_plus_feature"])


def _extract_ecgdeli_output_mat(cfg: dict[str, Any], row: pd.Series, output_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    features, audit = _extract_one(cfg, row)
    # Re-run the same extraction path only when the exploratory extraction succeeded,
    # then copy from the temporary MATLAB output is not possible because Stage 14E
    # intentionally cleans temp dirs. This function is kept as a status guard.
    return features, audit


def _matlab_output_for_record(cfg: dict[str, Any], row: pd.Series, output_mat: Path) -> dict[str, Any]:
    from src.data.extract_external_ecgdeli_feature_prototype import _load_signal, _matlab_script
    from src.data.run_ecgdeli_smoke import _matlab_escape
    import subprocess
    import tempfile
    from scipy.io import savemat

    with tempfile.TemporaryDirectory(prefix=f"ecgdeli_direct_{row['source_dataset']}_{row['record_id']}_") as tmp:
        tmpdir = Path(tmp)
        signal_mat = tmpdir / "input_signal.mat"
        script_path = tmpdir / "run_external_ecgdeli_direct_candidate.m"
        signal, fs = _load_signal(str(row["record_base"]))
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
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "output_exists": output_mat.exists(),
        }


def _aggregate_direct(mat_path: Path) -> dict[str, float]:
    mat = loadmat(mat_path)
    amplitude = np.asarray(mat["Amplitude_feature_12leads"], dtype=float)
    timing = np.asarray(mat["Timing_feature_12leads"], dtype=float)
    timing_sync = np.asarray(mat["Timing_feature_sync"], dtype=float)
    features: dict[str, float] = {}
    for lead_idx, lead in enumerate(LEADS):
        for base, (array_name, feature_idx) in LEADWISE_INDEX.items():
            source = amplitude if array_name == "Amplitude_feature_12leads" else timing
            if lead_idx < source.shape[0] and feature_idx < source.shape[2]:
                _assign_stat(features, f"{base}_{lead}", source[lead_idx, :, feature_idx])
    for base, feature_idx in GLOBAL_INDEX.items():
        if feature_idx < timing_sync.shape[1]:
            _assign_stat(features, f"{base}_Global", timing_sync[:, feature_idx])
    return features


def extract() -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    cfg = load_yaml("configs/ecgdeli_pipeline.yaml")
    out_dir = ensure_dir("data/processed/external")
    direct_names = _direct_feature_names()
    direct_set = set(direct_names)
    feature_tables: dict[str, pd.DataFrame] = {}
    audit_rows: list[dict[str, Any]] = []
    for dataset in DATASETS:
        manifest = pd.read_csv(out_dir / f"{dataset}_waveform_manifest.csv")
        sample = manifest[manifest["include_in_main_external_validation"].astype(bool)].head(N_RECORDS_PER_DATASET)
        rows: list[dict[str, Any]] = []
        for _, row in sample.iterrows():
            record_id = str(row["record_id"])
            output_mat = (Path("results/external/ecgdeli_direct_candidate_mat") / f"{dataset}_{record_id}.mat").resolve()
            status = _matlab_output_for_record(cfg, row, output_mat)
            features: dict[str, Any] = {"record_id": record_id, "source_dataset": dataset}
            if status["returncode"] == 0 and output_mat.exists():
                extracted = _aggregate_direct(output_mat)
                missing_direct = sorted(direct_set - set(extracted))
                for name in direct_names:
                    features[name] = extracted.get(name, np.nan)
                audit_rows.append(
                    {
                        "dataset": dataset,
                        "record_id": record_id,
                        "status": "generated_direct_candidate_features",
                        "n_generated_direct_features": len(extracted),
                        "n_expected_direct_features": len(direct_names),
                        "n_missing_direct_features": len(missing_direct),
                        "schema_exact_match": False,
                        "blocking_issue": "ptbxl_plus_exact_531_recipe_missing",
                        "notes": "Direct ECGdeli candidate features only; unresolved 111 frozen PTB-XL+ features are not generated.",
                    }
                )
            else:
                for name in direct_names:
                    features[name] = np.nan
                audit_rows.append(
                    {
                        "dataset": dataset,
                        "record_id": record_id,
                        "status": "failed",
                        "n_generated_direct_features": 0,
                        "n_expected_direct_features": len(direct_names),
                        "n_missing_direct_features": len(direct_names),
                        "schema_exact_match": False,
                        "blocking_issue": "ecgdeli_direct_candidate_extraction_failed;ptbxl_plus_exact_531_recipe_missing",
                        "notes": (str(status["stdout"]) + " " + str(status["stderr"]))[-1500:],
                    }
                )
            rows.append(features)
        table = pd.DataFrame(rows, columns=["record_id", "source_dataset", *direct_names])
        feature_tables[dataset] = table
        safe_to_csv(table, out_dir / f"{dataset}_ecgdeli_direct_candidate_features.csv")
    audit = pd.DataFrame(audit_rows)
    decision = pd.DataFrame(
        [
            {
                "n_generated_direct_features": len(direct_names),
                "n_required_features": 531,
                "n_missing_required_features": 531 - len(direct_names),
                "can_run_multimodal_external_validation": False,
                "blocking_issue": "ptbxl_plus_exact_531_recipe_missing",
                "notes": "Candidate files contain only direct ECGdeli-derived frozen-schema columns and are intentionally not registered as external structured feature tables.",
            }
        ]
    )
    return feature_tables, audit, decision


def _write_summary(feature_tables: dict[str, pd.DataFrame], audit: pd.DataFrame, decision: pd.DataFrame) -> None:
    overview = pd.DataFrame(
        [
            {
                "dataset": dataset,
                "n_rows": len(table),
                "n_columns": len(table.columns),
                "n_direct_feature_columns": len(table.columns) - 2,
                "output": f"data/processed/external/{dataset}_ecgdeli_direct_candidate_features.csv",
            }
            for dataset, table in feature_tables.items()
        ]
    )
    text = "\n".join(
        [
            "# Stage 14G External ECGdeli Direct Candidate Feature Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "A guarded candidate generator created only the 420 frozen-schema columns classified as `direct_ecgdeli` in Stage 14F. These files are incomplete candidate structured features and are not registered as official external multimodal inputs.",
            "",
            "## Outputs",
            "",
            overview.to_markdown(index=False),
            "",
            "## Audit",
            "",
            audit.to_markdown(index=False),
            "",
            "## Decision",
            "",
            decision.to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- The candidate files use real frozen PTB-XL+ column names for direct ECGdeli-derived features.",
            "- They intentionally omit 111 unresolved required features.",
            "- They must not be copied to `cpsc2018_structured_features.csv` or `chapman_structured_features.csv`.",
            "- Full multimodal external validation remains blocked.",
            "",
            "## Next Step",
            "",
            "Resolve QT_IntCorr, P_Morph, ST_Elev, and HA__Global definitions before generating complete 531-column external structured feature tables.",
        ]
    )
    write_markdown("results/stage14g_external_ecgdeli_direct_candidate_summary.md", text + "\n")


def main() -> None:
    ensure_dir("results/external/ecgdeli_direct_candidate_mat")
    ensure_dir("tables")
    feature_tables, audit, decision = extract()
    safe_to_csv(audit, "tables/table_external_ecgdeli_direct_candidate_audit.csv")
    safe_to_csv(decision, "tables/table_external_ecgdeli_direct_candidate_decision.csv")
    _write_summary(feature_tables, audit, decision)
    print("Wrote external ECGdeli direct candidate feature outputs.")


if __name__ == "__main__":
    main()
