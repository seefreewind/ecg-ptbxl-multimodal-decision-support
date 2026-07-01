from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


DATASET_ALIASES = {
    "cpsc2018": ["cpsc2018", "cpsc", "china physiological signal challenge"],
    "chapman": ["chapman", "shaoxing", "chapman_shaoxing", "chapman-shaoxing"],
}
WAVEFORM_SUFFIXES = {".mat", ".hea", ".dat", ".npy", ".npz"}
TABLE_SUFFIXES = {".csv", ".tsv", ".txt"}
SUPPORTED_SUFFIXES = WAVEFORM_SUFFIXES | TABLE_SUFFIXES
SEARCH_BASES = [Path("data/raw/external"), Path("data/external"), Path("../data/raw/external")]
AUDIT_COLUMNS = [
    "source_dataset",
    "source_label",
    "source_label_description",
    "mapped_ptbxl_superclass",
    "mapping_confidence",
    "include_in_main_external_validation",
    "include_in_sensitivity_analysis",
    "exclude_from_external_validation",
    "reason",
    "notes",
]
DISCOVERY_COLUMNS = [
    "dataset_candidate",
    "root_path",
    "n_waveform_files",
    "n_metadata_files",
    "n_label_files",
    "detected_formats",
    "sample_record_ids",
    "sample_labels",
    "status",
    "notes",
]


def _load_config(path: Path = Path("configs/data_external.yaml")) -> dict[str, Any]:
    if path.exists():
        return load_yaml(path)
    return {"external": {}, "task": {"ptbxl_superclasses": ["NORM", "MI", "STTC", "CD", "HYP"]}}


def _candidate_roots(dataset: str, cfg: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    dataset_cfg = cfg.get("external", {}).get(dataset, {})
    for key in ["root_dir", "label_file"]:
        value = dataset_cfg.get(key)
        if value and key == "root_dir":
            roots.append(Path(value))
    for value in dataset_cfg.get("alternate_root_dirs", []) or []:
        roots.append(Path(value))
    aliases = DATASET_ALIASES.get(dataset, [dataset])
    for base in SEARCH_BASES:
        for alias in aliases:
            roots.append(base / alias)
        if base.exists():
            for child in base.iterdir():
                lowered = child.name.lower()
                if any(alias in lowered for alias in aliases):
                    roots.append(child)
    unique = []
    seen = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return unique


def _is_label_file(path: Path) -> bool:
    lowered = path.name.lower()
    if path.suffix.lower() == ".hea":
        try:
            return "# dx:" in path.read_text(errors="ignore").lower()
        except Exception:
            return False
    return path.suffix.lower() in TABLE_SUFFIXES and any(
        token in lowered for token in ["label", "reference", "diagn", "dx", "scp", "annot", "metadata", "condition", "snomed"]
    )


def _is_metadata_file(path: Path) -> bool:
    lowered = path.name.lower()
    if path.suffix.lower() == ".hea":
        return True
    return path.suffix.lower() in TABLE_SUFFIXES and any(
        token in lowered for token in ["meta", "record", "info", "subject", "patient", "attributes"]
    )


def _sample_labels(files: list[Path], limit: int = 12) -> str:
    labels: list[str] = []
    for path in files[:25]:
        try:
            if path.suffix.lower() == ".hea":
                for line in path.read_text(errors="ignore").splitlines():
                    if line.lower().startswith("# dx:"):
                        labels.extend([item.strip() for item in line.split(":", 1)[1].split(",") if item.strip()])
                continue
            if path.suffix.lower() == ".csv":
                df = pd.read_csv(path, nrows=20)
            elif path.suffix.lower() == ".tsv":
                df = pd.read_csv(path, sep="\t", nrows=20)
            else:
                lines = path.read_text(errors="ignore").splitlines()[:20]
                labels.extend([line.strip()[:80] for line in lines if line.strip()])
                continue
            label_cols = [col for col in df.columns if any(token in str(col).lower() for token in ["label", "diagn", "dx", "rhythm", "class"])]
            for col in label_cols[:3]:
                labels.extend(df[col].dropna().astype(str).head(10).tolist())
        except Exception:
            continue
    deduped = []
    for label in labels:
        if label not in deduped:
            deduped.append(label)
    return "; ".join(deduped[:limit])


def _discover_dataset(dataset: str, cfg: dict[str, Any]) -> dict[str, Any]:
    roots = _candidate_roots(dataset, cfg)
    existing = [root for root in roots if root.exists()]
    if not existing:
        return {
            "dataset_candidate": dataset,
            "root_path": str(roots[0]) if roots else "",
            "n_waveform_files": 0,
            "n_metadata_files": 0,
            "n_label_files": 0,
            "detected_formats": "",
            "sample_record_ids": "",
            "sample_labels": "",
            "status": "missing",
            "notes": "External raw data are missing. Place CPSC2018 and/or Chapman-Shaoxing under data/raw/external/ before formal external validation.",
        }
    root = existing[0]
    files = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES]
    waveform_files = [path for path in files if path.suffix.lower() in WAVEFORM_SUFFIXES]
    label_files = [path for path in files if _is_label_file(path)]
    metadata_files = [path for path in files if _is_metadata_file(path)]
    sample_ids = [path.stem for path in waveform_files[:8]]
    formats = sorted({path.suffix.lower().lstrip(".") for path in files})
    status = "found" if waveform_files or label_files or metadata_files else "empty_directory"
    notes = "Candidate external dataset found; readiness still depends on waveform and label compatibility." if status == "found" else "Directory exists but no supported files were found."
    return {
        "dataset_candidate": dataset,
        "root_path": str(root),
        "n_waveform_files": len(waveform_files),
        "n_metadata_files": len(metadata_files),
        "n_label_files": len(label_files),
        "detected_formats": ";".join(formats),
        "sample_record_ids": ";".join(sample_ids),
        "sample_labels": _sample_labels(label_files),
        "status": status,
        "notes": notes,
    }


def build_label_mapping_audit() -> pd.DataFrame:
    rows = [
        ["CPSC2018", "Normal", "Normal ECG/control label", "NORM", "high", True, False, False, "Direct normal label if annotation confirms absence of major abnormality.", "Confirm exact spelling in placed label file."],
        ["CPSC2018", "I-AVB", "First-degree atrioventricular block", "CD", "high", True, False, False, "Specific conduction disturbance.", "High-confidence CD if source dictionary matches CPSC2018 convention."],
        ["CPSC2018", "LBBB", "Left bundle branch block", "CD", "high", True, False, False, "Specific bundle branch block.", ""],
        ["CPSC2018", "RBBB", "Right bundle branch block", "CD", "high", True, False, False, "Specific bundle branch block.", ""],
        ["CPSC2018", "STD", "ST depression", "STTC", "medium", False, True, False, "Likely ST-T change but should remain sensitivity-only until source definition is audited.", "Do not combine with infarction labels."],
        ["CPSC2018", "STE", "ST elevation", "STTC", "low", False, False, True, "ST elevation may reflect acute ischemia/infarction and is not a safe PTB-XL STTC/MI mapping by itself.", ""],
        ["CPSC2018", "AF", "Atrial fibrillation", "", "exclude", False, False, True, "Arrhythmia label does not map cleanly to NORM/MI/STTC/CD/HYP.", ""],
        ["CPSC2018", "PAC", "Premature atrial contraction", "", "exclude", False, False, True, "Ectopy label outside target superclass task.", ""],
        ["CPSC2018", "PVC", "Premature ventricular contraction", "", "exclude", False, False, True, "Ectopy label outside target superclass task.", ""],
        ["Chapman-Shaoxing", "Normal ECG", "Normal ECG/control label", "NORM", "high", True, False, False, "Direct normal label if annotation confirms no major abnormality.", "Sinus rhythm alone should not be treated as high-confidence normal."],
        ["Chapman-Shaoxing", "Sinus rhythm", "Sinus rhythm without explicit normal-control definition", "NORM", "medium", False, True, False, "Sinus rhythm may coexist with other abnormalities.", "Sensitivity analysis only unless dataset defines it as normal."],
        ["Chapman-Shaoxing", "Myocardial infarction", "Myocardial infarction diagnosis", "MI", "high", True, False, False, "Direct MI label when exact diagnosis is available.", "Confirm source dictionary and acute/old MI wording."],
        ["Chapman-Shaoxing", "Old myocardial infarction", "Old myocardial infarction diagnosis", "MI", "high", True, False, False, "Direct infarction label.", ""],
        ["Chapman-Shaoxing", "ST-T abnormality", "ST/T wave abnormality", "STTC", "medium", False, True, False, "Potential STTC mapping but may be nonspecific or mixed.", "Main analysis only if exact source definition is audited."],
        ["Chapman-Shaoxing", "RBBB", "Right bundle branch block", "CD", "high", True, False, False, "Specific conduction disturbance.", ""],
        ["Chapman-Shaoxing", "LBBB", "Left bundle branch block", "CD", "high", True, False, False, "Specific conduction disturbance.", ""],
        ["Chapman-Shaoxing", "AV block", "Atrioventricular block", "CD", "high", True, False, False, "Specific conduction disturbance.", ""],
        ["Chapman-Shaoxing", "Left ventricular hypertrophy", "Left ventricular hypertrophy", "HYP", "high", True, False, False, "Direct hypertrophy label.", "Voltage-only abnormality should be downgraded to medium."],
        ["Chapman-Shaoxing", "Atrial fibrillation", "Atrial fibrillation rhythm label", "", "exclude", False, False, True, "Rhythm label outside PTB-XL five-superclass target.", ""],
    ]
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def _write_label_mapping_plan(audit: pd.DataFrame) -> None:
    covered = audit[audit["mapping_confidence"].eq("high")].groupby("source_dataset")["mapped_ptbxl_superclass"].apply(lambda s: sorted(set(x for x in s if x))).to_dict()
    lines = [
        "# External Label Mapping Plan",
        "",
        "Generated date: " + date.today().isoformat(),
        "",
        "## Scope",
        "",
        "This is a draft compatibility plan for future external validation on CPSC2018 and Chapman-Shaoxing. It is not an external validation result.",
        "",
        "Target PTB-XL superclass labels: `NORM`, `MI`, `STTC`, `CD`, `HYP`.",
        "",
        "## Conservative Mapping Rules",
        "",
        "- Only `high` confidence labels may enter the main external-validation analysis.",
        "- `medium` confidence labels are sensitivity-analysis only.",
        "- `low` and `exclude` labels must not enter the main analysis.",
        "- External validation may use a high-confidence label subset; it must not force all five PTB-XL classes.",
        "- If actual external label files differ from this draft, the audit table must be revised before evaluation.",
        "",
        "## Dataset Coverage From Draft Audit",
        "",
    ]
    for dataset in ["CPSC2018", "Chapman-Shaoxing"]:
        labels = covered.get(dataset, [])
        missing = sorted(set(["NORM", "MI", "STTC", "CD", "HYP"]) - set(labels))
        lines.append(f"- {dataset}: high-confidence draft coverage = {', '.join(labels) if labels else 'none'}; not safely covered = {', '.join(missing) if missing else 'none'}.")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- CPSC2018 is expected to support high-confidence `NORM` and `CD` mappings, while MI and HYP are not safely covered by the common nine-label CPSC2018 task.",
            "- Chapman-Shaoxing may support broader mappings, but this remains conditional on the actual annotation dictionary present in the downloaded files.",
            "- ST/T labels should be treated carefully because ischemia, infarction, and nonspecific repolarization abnormalities can be mixed in external datasets.",
            "",
            "## Audit Table",
            "",
            "See `tables/table_external_label_mapping_audit.csv`.",
        ]
    )
    write_markdown("docs/EXTERNAL_LABEL_MAPPING_PLAN.md", "\n".join(lines) + "\n")


def _write_report(candidates: pd.DataFrame) -> None:
    missing = candidates[candidates["status"].eq("missing")]
    lines = [
        "# External Dataset Discovery Report",
        "",
        "Generated date: " + date.today().isoformat(),
        "",
        "## Search Scope",
        "",
        "- `data/raw/external/`",
        "- `data/external/`",
        "- `../data/raw/external/`",
        "",
        "## Candidate Summary",
        "",
        candidates.to_markdown(index=False),
        "",
    ]
    if len(missing) == len(candidates):
        lines.extend(
            [
                "## Blocking Message",
                "",
                "External raw data are missing. Place CPSC2018 and/or Chapman-Shaoxing under data/raw/external/ before formal external validation.",
                "",
            ]
        )
    write_markdown("results/external/external_dataset_discovery_report.md", "\n".join(lines))


def main() -> None:
    ensure_dir("results/external")
    ensure_dir("tables")
    cfg = _load_config()
    rows = [_discover_dataset(dataset, cfg) for dataset in ["cpsc2018", "chapman"]]
    candidates = pd.DataFrame(rows, columns=DISCOVERY_COLUMNS)
    safe_to_csv(candidates, "results/external/external_dataset_candidates.csv")
    audit = build_label_mapping_audit()
    safe_to_csv(audit, "tables/table_external_label_mapping_audit.csv")
    _write_label_mapping_plan(audit)
    _write_report(candidates)
    print("Wrote external dataset discovery report and label mapping audit.")


if __name__ == "__main__":
    main()
