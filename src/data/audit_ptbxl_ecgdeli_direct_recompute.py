from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.data.extract_external_ecgdeli_direct_candidate import _aggregate_direct, _direct_feature_names, _matlab_output_for_record
from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


N_SAMPLE_RECORDS = 3


def _sample_ptbxl_records() -> pd.DataFrame:
    meta = pd.read_csv("data/raw/ptbxl/ptbxl_database.csv")
    rows = []
    for _, row in meta.sort_values("ecg_id").iterrows():
        filename_hr = str(row.get("filename_hr", ""))
        record_base = Path("data/raw/ptbxl") / filename_hr
        if (record_base.with_suffix(".hea")).exists() and (record_base.with_suffix(".dat")).exists():
            rows.append(
                {
                    "ecg_id": int(row["ecg_id"]),
                    "record_id": str(int(row["ecg_id"])),
                    "source_dataset": "ptbxl_recompute_audit",
                    "record_base": str(record_base),
                }
            )
        if len(rows) >= N_SAMPLE_RECORDS:
            break
    if len(rows) < N_SAMPLE_RECORDS:
        raise RuntimeError("Not enough PTB-XL HR waveform records found for recompute audit.")
    return pd.DataFrame(rows)


def _recompute_candidates() -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = load_yaml("configs/ecgdeli_pipeline.yaml")
    direct_names = _direct_feature_names()
    mat_dir = ensure_dir("results/ptbxl_ecgdeli_direct_recompute_mat")
    rows = []
    audit_rows: list[dict[str, Any]] = []
    sample = _sample_ptbxl_records()
    for _, row in sample.iterrows():
        ecg_id = int(row["ecg_id"])
        output_mat = (mat_dir / f"ptbxl_{ecg_id}.mat").resolve()
        status = _matlab_output_for_record(cfg, row, output_mat)
        out: dict[str, Any] = {"ecg_id": ecg_id, "record_id": str(ecg_id), "source_dataset": "ptbxl_recompute_audit"}
        if status["returncode"] == 0 and output_mat.exists():
            features = _aggregate_direct(output_mat)
            for name in direct_names:
                out[name] = features.get(name, np.nan)
            audit_rows.append(
                {
                    "ecg_id": ecg_id,
                    "status": "generated_direct_candidate_features",
                    "n_generated_direct_features": len(features),
                    "n_expected_direct_features": len(direct_names),
                    "n_missing_direct_features": len(set(direct_names) - set(features)),
                    "notes": "PTB-XL HR waveform recomputed with local MATLAB/ECGdeli direct candidate generator.",
                }
            )
        else:
            for name in direct_names:
                out[name] = np.nan
            audit_rows.append(
                {
                    "ecg_id": ecg_id,
                    "status": "failed",
                    "n_generated_direct_features": 0,
                    "n_expected_direct_features": len(direct_names),
                    "n_missing_direct_features": len(direct_names),
                    "notes": (str(status["stdout"]) + " " + str(status["stderr"]))[-1500:],
                }
            )
        rows.append(out)
    return pd.DataFrame(rows, columns=["ecg_id", "record_id", "source_dataset", *direct_names]), pd.DataFrame(audit_rows)


def _compare_to_official(candidates: pd.DataFrame) -> pd.DataFrame:
    direct_names = _direct_feature_names()
    official = pd.read_csv("data/raw/ptbxl_plus/features/ecgdeli_features.csv")
    merged = candidates[["ecg_id", *direct_names]].merge(official[["ecg_id", *direct_names]], on="ecg_id", suffixes=("_recomputed", "_official"))
    rows = []
    for feature in direct_names:
        a = pd.to_numeric(merged[f"{feature}_recomputed"], errors="coerce").to_numpy(dtype=float)
        b = pd.to_numeric(merged[f"{feature}_official"], errors="coerce").to_numpy(dtype=float)
        mask = np.isfinite(a) & np.isfinite(b)
        diff = a[mask] - b[mask]
        rows.append(
            {
                "feature": feature,
                "n_pairs": int(mask.sum()),
                "official_nonmissing": int(np.isfinite(b).sum()),
                "recomputed_nonmissing": int(np.isfinite(a).sum()),
                "mean_abs_error": float(np.mean(np.abs(diff))) if diff.size else np.nan,
                "median_abs_error": float(np.median(np.abs(diff))) if diff.size else np.nan,
                "max_abs_error": float(np.max(np.abs(diff))) if diff.size else np.nan,
                "allclose_atol_1e_6": bool(diff.size and np.allclose(a[mask], b[mask], atol=1e-6, rtol=1e-6)),
            }
        )
    return pd.DataFrame(rows)


def _decision(comparison: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    generated_ok = bool((audit["status"] == "generated_direct_candidate_features").all())
    comparable = comparison[comparison["n_pairs"].astype(int) > 0]
    exact_direct = bool(generated_ok and len(comparable) == 420 and comparable["allclose_atol_1e_6"].astype(bool).all())
    return pd.DataFrame(
        [
            {
                "can_claim_exact_direct_420_recompute": exact_direct,
                "can_claim_exact_ptbxl_plus_recipe": False,
                "can_run_multimodal_external_validation": False,
                "n_sample_records": int(audit.shape[0]),
                "n_direct_features_compared": int(len(comparable)),
                "n_direct_features_allclose": int(comparable["allclose_atol_1e_6"].astype(bool).sum()) if len(comparable) else 0,
                "median_feature_mae": float(comparable["mean_abs_error"].median()) if len(comparable) else np.nan,
                "blocking_issue": "ptbxl_plus_exact_531_recipe_missing",
                "notes": "Small-sample recomputation audit only; unresolved 111 features and any direct-feature discrepancies block exact 531-feature claims.",
            }
        ]
    )


def _write_summary(candidates: pd.DataFrame, audit: pd.DataFrame, comparison: pd.DataFrame, decision: pd.DataFrame) -> None:
    by_error = comparison.sort_values("mean_abs_error", ascending=False).head(15)
    text = "\n".join(
        [
            "# Stage 14H PTB-XL ECGdeli Direct Recompute Audit Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "A small PTB-XL HR waveform sample was recomputed with the local MATLAB/ECGdeli direct candidate generator and compared against the official PTB-XL+ `ecgdeli_features.csv` table.",
            "",
            "This is a reverse-engineering audit only. It does not establish an exact PTB-XL+ 531-feature recipe.",
            "",
            "## Recompute Audit",
            "",
            audit.to_markdown(index=False),
            "",
            "## Decision",
            "",
            decision.to_markdown(index=False),
            "",
            "## Largest Direct-Feature Differences",
            "",
            by_error.to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- Local ECGdeli can recompute direct candidate features from PTB-XL HR waveforms.",
            "- Numeric agreement with official PTB-XL+ must be audited before any exact-recipe claim.",
            "- Complete 531-column external structured features remain blocked by unresolved QT_IntCorr, P_Morph, ST_Elev, and HA__Global definitions.",
            "",
            "## Outputs",
            "",
            "- `data/processed/ptbxl_ecgdeli_direct_recomputed_sample.csv`",
            "- `tables/table_ptbxl_ecgdeli_direct_recompute_audit.csv`",
            "- `tables/table_ptbxl_ecgdeli_direct_recompute_comparison.csv`",
            "- `tables/table_ptbxl_ecgdeli_direct_recompute_decision.csv`",
        ]
    )
    write_markdown("results/stage14h_ptbxl_ecgdeli_direct_recompute_audit_summary.md", text + "\n")


def main() -> None:
    ensure_dir("data/processed")
    ensure_dir("tables")
    ensure_dir("results")
    candidates, audit = _recompute_candidates()
    comparison = _compare_to_official(candidates)
    decision = _decision(comparison, audit)
    safe_to_csv(candidates, "data/processed/ptbxl_ecgdeli_direct_recomputed_sample.csv")
    safe_to_csv(audit, "tables/table_ptbxl_ecgdeli_direct_recompute_audit.csv")
    safe_to_csv(comparison, "tables/table_ptbxl_ecgdeli_direct_recompute_comparison.csv")
    safe_to_csv(decision, "tables/table_ptbxl_ecgdeli_direct_recompute_decision.csv")
    _write_summary(candidates, audit, comparison, decision)
    print("Wrote PTB-XL ECGdeli direct recompute audit outputs.")


if __name__ == "__main__":
    main()
