from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


PROCESSED_COLUMNS = [
    "record_id",
    "source_dataset",
    "waveform_path",
    "sampling_rate_original",
    "sampling_rate_target",
    "duration_original",
    "target_length",
    "lead_order",
    "mapped_NORM",
    "mapped_MI",
    "mapped_STTC",
    "mapped_CD",
    "mapped_HYP",
    "include_in_main_external_validation",
    "include_in_sensitivity_analysis",
    "mapping_notes",
    "status",
]
MODE_COLUMNS = [
    "dataset",
    "external_data_found",
    "high_confidence_labels_available",
    "high_confidence_ptbxl_superclasses",
    "waveform_compatible",
    "structured_features_compatible",
    "recommended_external_validation_mode",
    "full_multimodal_external_validation_allowed",
    "signal_only_external_validation_allowed",
    "blocking_issue",
    "notes",
]


def _load_config() -> dict[str, Any]:
    return load_yaml("configs/data_external.yaml") if Path("configs/data_external.yaml").exists() else {}


def _write_empty_processed(dataset: str, status: str) -> None:
    out_dir = ensure_dir("data/processed/external")
    row = {col: "" for col in PROCESSED_COLUMNS}
    row.update({"source_dataset": dataset, "status": status})
    df = pd.DataFrame([row], columns=PROCESSED_COLUMNS)
    for suffix in ["index", "labels_mapped", "waveform_manifest"]:
        safe_to_csv(df, out_dir / f"{dataset}_{suffix}.csv")


def _write_found_processed(dataset: str, root: Path, cfg: dict[str, Any]) -> None:
    out_dir = ensure_dir("data/processed/external")
    target_fs = cfg.get("external", {}).get(dataset, {}).get("target_sampling_rate", 100)
    target_len = int(target_fs) * int(cfg.get("external", {}).get(dataset, {}).get("target_duration_seconds", 10))
    waveform_files = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".mat", ".hea", ".dat", ".npy", ".npz"}]
    rows = []
    for path in waveform_files:
        rows.append(
            {
                "record_id": path.stem,
                "source_dataset": dataset,
                "waveform_path": str(path),
                "sampling_rate_original": "",
                "sampling_rate_target": target_fs,
                "duration_original": "",
                "target_length": target_len,
                "lead_order": "",
                "mapped_NORM": "",
                "mapped_MI": "",
                "mapped_STTC": "",
                "mapped_CD": "",
                "mapped_HYP": "",
                "include_in_main_external_validation": False,
                "include_in_sensitivity_analysis": False,
                "mapping_notes": "Skeleton only; actual labels must be mapped before evaluation.",
                "status": "skeleton_not_evaluated",
            }
        )
    if not rows:
        rows = [{col: "" for col in PROCESSED_COLUMNS}]
        rows[0].update({"source_dataset": dataset, "status": "no_waveform_files_found"})
    df = pd.DataFrame(rows, columns=PROCESSED_COLUMNS)
    for suffix in ["index", "labels_mapped", "waveform_manifest"]:
        safe_to_csv(df, out_dir / f"{dataset}_{suffix}.csv")


def _high_confidence_labels(audit: pd.DataFrame, source_dataset: str) -> list[str]:
    rows = audit[
        audit["source_dataset"].eq(source_dataset)
        & audit["mapping_confidence"].eq("high")
        & audit["include_in_main_external_validation"].astype(bool)
    ]
    return sorted(set(str(value) for value in rows["mapped_ptbxl_superclass"] if str(value)))


def _decide_modes(candidates: pd.DataFrame, waveform: pd.DataFrame, structured: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dataset_names = {"cpsc2018": "CPSC2018", "chapman": "Chapman-Shaoxing"}
    for dataset, source_name in dataset_names.items():
        cand = candidates[candidates["dataset_candidate"].eq(dataset)]
        wav = waveform[waveform["dataset"].eq(dataset)]
        feat = structured[structured["dataset"].eq(dataset)]
        found = bool((not cand.empty) and str(cand.iloc[0]["status"]) == "found")
        waveform_ok = bool((not wav.empty) and bool(wav.iloc[0]["compatible_with_signal_model"]))
        structured_ok = bool((not feat.empty) and bool(feat.iloc[0]["matches_ptbxl_plus_features"]))
        high_labels = _high_confidence_labels(audit, source_name)
        labels_ok = bool(found and high_labels)
        blocking = []
        if not found:
            blocking.append("external_raw_data_missing")
        if found and not labels_ok:
            blocking.append("no_confirmed_high_confidence_labels_in_actual_files")
        if found and not waveform_ok:
            issue = "" if wav.empty else str(wav.iloc[0]["blocking_issue"])
            blocking.append(issue or "waveform_not_compatible")
        if found and waveform_ok and labels_ok and structured_ok:
            mode = "multimodal_full"
        elif found and waveform_ok and labels_ok and not structured_ok:
            mode = "signal_only_main"
            blocking.append("external_structured_features_missing_for_multimodal")
        else:
            mode = "not_ready"
        rows.append(
            {
                "dataset": dataset,
                "external_data_found": found,
                "high_confidence_labels_available": labels_ok,
                "high_confidence_ptbxl_superclasses": ";".join(high_labels),
                "waveform_compatible": waveform_ok,
                "structured_features_compatible": structured_ok,
                "recommended_external_validation_mode": mode,
                "full_multimodal_external_validation_allowed": bool(mode == "multimodal_full"),
                "signal_only_external_validation_allowed": bool(mode == "signal_only_main"),
                "blocking_issue": ";".join(dict.fromkeys([item for item in blocking if item])),
                "notes": "Readiness decision only; no external model evaluation was run.",
            }
        )
    return pd.DataFrame(rows, columns=MODE_COLUMNS)


def _update_figure9_source_data(candidates: pd.DataFrame, waveform: pd.DataFrame, structured: pd.DataFrame, modes: pd.DataFrame, audit: pd.DataFrame) -> None:
    source = ensure_dir("figures/source_data")
    readiness = modes.merge(candidates[["dataset_candidate", "n_waveform_files", "n_label_files", "n_metadata_files", "status"]], left_on="dataset", right_on="dataset_candidate", how="left")
    readiness = readiness.merge(waveform[["dataset", "lead_count", "sampling_rate_detected", "duration_detected", "compatible_with_signal_model"]], on="dataset", how="left")
    readiness = readiness.merge(structured[["dataset", "has_external_structured_features", "matches_ptbxl_plus_features"]], on="dataset", how="left")
    readiness = readiness.drop(columns=["dataset_candidate"])
    safe_to_csv(readiness, source / "fig9_external_validation_readiness.csv")
    safe_to_csv(audit, source / "fig9_external_label_mapping.csv")
    manifest_path = source / "FIGURE_SOURCE_DATA_MANIFEST.csv"
    manifest = pd.read_csv(manifest_path) if manifest_path.exists() else pd.DataFrame(columns=["figure", "panel", "source_file", "description", "generated_from", "script", "status", "last_updated", "notes"])
    manifest = manifest[manifest["figure"].ne("Figure 9")]
    new_rows = pd.DataFrame(
        [
            {
                "figure": "Figure 9",
                "panel": "A/C/D",
                "source_file": "figures/source_data/fig9_external_validation_readiness.csv",
                "description": "External dataset availability, waveform compatibility, and recommended validation mode",
                "generated_from": "Stage 13A external readiness audit",
                "script": "scripts/14c_prepare_external_waveforms.sh",
                "status": "ready",
                "last_updated": date.today().isoformat(),
                "notes": "Readiness only; not external validation results.",
            },
            {
                "figure": "Figure 9",
                "panel": "B",
                "source_file": "figures/source_data/fig9_external_label_mapping.csv",
                "description": "External label mapping confidence audit",
                "generated_from": "Stage 13A external readiness audit",
                "script": "scripts/14a_discover_external_datasets.sh",
                "status": "ready",
                "last_updated": date.today().isoformat(),
                "notes": "Draft mapping table requiring confirmation against actual label files.",
            },
        ]
    )
    pd.concat([manifest, new_rows], ignore_index=True).to_csv(manifest_path, index=False)


def _update_master_plan() -> None:
    path = Path("docs/FIGURE_MASTER_PLAN.md")
    text = path.read_text() if path.exists() else "# Figure Master Plan\n"
    if "## Figure 9. External validation readiness and label compatibility" in text:
        return
    addition = """

## Figure 9. External validation readiness and label compatibility

Panels:
A. External dataset availability
B. Label mapping confidence
C. Waveform compatibility
D. Recommended validation mode

Required source data:
- figures/source_data/fig9_external_validation_readiness.csv
- figures/source_data/fig9_external_label_mapping.csv

Note:
Figure 9 is a readiness and compatibility audit, not an external validation result figure.
"""
    path.write_text(text.rstrip() + addition + "\n")


def _write_mode_report(modes: pd.DataFrame) -> None:
    write_markdown(
        "results/external/external_validation_mode_decision.md",
        "\n".join(
            [
                "# External Validation Mode Decision",
                "",
                "Generated date: " + date.today().isoformat(),
                "",
                modes.to_markdown(index=False),
                "",
                "Allowed modes: `signal_only_main`, `multimodal_full`, `multimodal_missing_modality`, `external_feature_extraction_required`, `not_ready`.",
                "",
                "Do not run fair concat or gated fusion externally unless structured feature compatibility is confirmed or a pre-specified missing-modality pathway exists.",
            ]
        )
        + "\n",
    )


def _write_summary(candidates: pd.DataFrame, waveform: pd.DataFrame, structured: pd.DataFrame, audit: pd.DataFrame, modes: pd.DataFrame) -> None:
    def display(value: object, fallback: str = "unknown") -> str:
        if pd.isna(value) or str(value) == "":
            return fallback
        return str(value)

    def dataset_block(dataset: str, source_name: str) -> list[str]:
        cand = candidates[candidates["dataset_candidate"].eq(dataset)].iloc[0]
        wav = waveform[waveform["dataset"].eq(dataset)].iloc[0]
        feat = structured[structured["dataset"].eq(dataset)].iloc[0]
        mode = modes[modes["dataset"].eq(dataset)].iloc[0]
        high = _high_confidence_labels(audit, source_name)
        medium = audit[audit["source_dataset"].eq(source_name) & audit["mapping_confidence"].eq("medium")]["source_label"].tolist()
        excluded = audit[audit["source_dataset"].eq(source_name) & audit["mapping_confidence"].isin(["low", "exclude"])]["source_label"].tolist()
        missing_super = sorted(set(["NORM", "MI", "STTC", "CD", "HYP"]) - set(high))
        return [
            f"### {source_name}",
            "",
            f"- availability: {cand['status']}",
            f"- root path: `{cand['root_path']}`",
            f"- waveform files: {cand['n_waveform_files']}",
            f"- label files: {cand['n_label_files']}",
            f"- metadata files: {cand['n_metadata_files']}",
            f"- draft high-confidence mapped labels: {', '.join(high) if high else 'none confirmed'}",
            f"- medium-confidence labels: {', '.join(map(str, medium)) if medium else 'none'}",
            f"- excluded/low-confidence labels: {', '.join(map(str, excluded)) if excluded else 'none'}",
            f"- PTB-XL superclasses not safely covered by high-confidence draft mapping: {', '.join(missing_super) if missing_super else 'none'}",
            f"- lead count: {display(wav['lead_count'])}",
            f"- sampling rate: {display(wav['sampling_rate_detected'])}",
            f"- duration: {display(wav['duration_detected'])}",
            f"- compatible with signal-only model: {wav['compatible_with_signal_model']}",
            f"- structured features available: {feat['has_external_structured_features']}",
            f"- full multimodal allowed: {mode['full_multimodal_external_validation_allowed']}",
            f"- recommended mode: `{mode['recommended_external_validation_mode']}`",
            f"- blocking issue: {display(mode['blocking_issue'], 'none')}",
            "",
        ]

    stage_status = "completed" if Path("results/external/external_dataset_candidates.csv").exists() else "partially completed"
    lines = [
        "# Stage 13A External Validation Readiness Summary",
        "",
        "Date: " + date.today().isoformat(),
        "",
        "## 1. Stage Status",
        "",
        f"- {stage_status}",
        "- This stage is a readiness audit only. No formal external validation was run.",
        "",
        "## 2. External Dataset Availability",
        "",
    ]
    lines.extend(dataset_block("cpsc2018", "CPSC2018"))
    lines.extend(dataset_block("chapman", "Chapman-Shaoxing"))
    lines.extend(
        [
            "## 3. Label Mapping Audit",
            "",
            "- High-confidence labels may enter main external validation only after actual external label files confirm the same semantics.",
            "- Medium-confidence labels are sensitivity-analysis only.",
            "- Low-confidence and excluded labels must not enter main external validation.",
            "- Main external validation may use a subset of PTB-XL superclasses.",
            "",
            "## 4. Waveform Compatibility",
            "",
            waveform.to_markdown(index=False),
            "",
            "## 5. Structured Feature Compatibility",
            "",
            structured.to_markdown(index=False),
            "",
            "## 6. Recommended External Validation Mode",
            "",
            modes.to_markdown(index=False),
            "",
            "## 7. Blocking Issues",
            "",
        ]
    )
    blockers = [str(item) for item in modes["blocking_issue"] if str(item)]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## 8. What Must Not Be Claimed Yet",
            "",
            "- no external generalization claim",
            "- no clinical-readiness claim",
            "- no multimodal external validation claim unless structured features are compatible",
            "",
            "## 9. Next Recommended Step",
            "",
        ]
    )
    if not bool(modes["external_data_found"].any()):
        lines.append("- place external raw data under `data/raw/external/`.")
    elif (modes["recommended_external_validation_mode"] == "signal_only_main").any():
        lines.append("- proceed to signal-only external validation for compatible datasets only.")
    elif (modes["recommended_external_validation_mode"] == "external_feature_extraction_required").any():
        lines.append("- implement structured ECG feature extraction before multimodal external validation.")
    elif (modes["recommended_external_validation_mode"] == "multimodal_full").any():
        lines.append("- proceed to full external validation for compatible datasets.")
    else:
        lines.append("- fix label mapping or waveform compatibility first.")
    write_markdown("results/stage13a_external_readiness_summary.md", "\n".join(lines) + "\n")


def main() -> None:
    ensure_dir("data/processed/external")
    ensure_dir("results/external")
    ensure_dir("tables")
    cfg = _load_config()
    candidates = pd.read_csv("results/external/external_dataset_candidates.csv")
    waveform = pd.read_csv("tables/table_external_waveform_compatibility.csv")
    structured = pd.read_csv("tables/table_external_structured_feature_compatibility.csv")
    audit = pd.read_csv("tables/table_external_label_mapping_audit.csv")
    for dataset in ["cpsc2018", "chapman"]:
        row = candidates[candidates["dataset_candidate"].eq(dataset)].iloc[0]
        root = Path(str(row["root_path"]))
        if str(row["status"]) == "found" and root.exists():
            _write_found_processed(dataset, root, cfg)
        else:
            _write_empty_processed(dataset, "external_raw_data_missing")
    modes = _decide_modes(candidates, waveform, structured, audit)
    safe_to_csv(modes, "tables/table_external_validation_mode_decision.csv")
    _write_mode_report(modes)
    _update_figure9_source_data(candidates, waveform, structured, modes, audit)
    _update_master_plan()
    _write_summary(candidates, waveform, structured, audit, modes)
    print("Wrote external waveform skeletons, mode decision, Figure 9 source data, and Stage 13A summary.")


if __name__ == "__main__":
    main()
