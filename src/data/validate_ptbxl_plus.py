from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, load_yaml, project_root_from_config, read_table_auto, resolve_path, safe_to_csv, write_markdown

ID_CANDIDATES = ["ecg_id", "record_id", "id", "ECG_ID"]
FEATURE_SUFFIXES = [".csv", ".tsv", ".parquet", ".feather", ".pkl", ".pickle"]
ECG_FEATURE_KEYWORDS = ["qrs", "qt", "qtc", "pr", "rr", "axis", "amplitude", "duration", "interval", "rate"]
LABEL_LEAKAGE_KEYWORDS = ["diagnostic", "statement", "snomed", "scp", "label", "target", "class", "subclass"]
ALLOWED_FEATURE_FILES = {
    "features/ecgdeli_features.csv": 300,
    "features/12sl_features.csv": 200,
    "features/unig_features.csv": 100,
}
LEAKAGE_EXCLUSION_MESSAGE = (
    "Excluded because this file contains diagnostic statements, label mappings, "
    "or PTB-XL-derived annotations and may introduce target leakage."
)
MISSING_MESSAGE = "PTB-XL+ structured features are still missing. Multimodal modeling is not allowed yet."


def _normalise_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalise_id_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def identify_id_column(columns: list[str]) -> str:
    lower = {str(col).lower(): str(col) for col in columns}
    for candidate in ID_CANDIDATES:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return ""


def classify_file_role(path: Path, ptbxl_plus_root: Path | None = None) -> tuple[str, bool, str]:
    rel = _normalise_rel(path, ptbxl_plus_root) if ptbxl_plus_root is not None else path.as_posix()
    rel_lower = rel.lower()
    name_lower = path.name.lower()
    if "structured_audit" in rel_lower or "confirmed_pair_structured_audit_packet" in rel_lower:
        return "unrelated", False, "unrelated structured_audit file is not PTB-XL+"
    if rel_lower in ALLOWED_FEATURE_FILES:
        return "allowed_feature_table", True, "Official PTB-XL+ leakage-safe feature table."
    if "/labels/" in f"/{rel_lower}" or rel_lower.startswith("labels/"):
        if "mapping/" in rel_lower:
            return "mapping_file", False, LEAKAGE_EXCLUSION_MESSAGE
        if "statement" in rel_lower or "snomed" in rel_lower:
            return "label_or_diagnostic_statement", False, LEAKAGE_EXCLUSION_MESSAGE
        return "label_or_diagnostic_statement", False, LEAKAGE_EXCLUSION_MESSAGE
    if any(keyword in rel_lower for keyword in ["statements", "snomed", "mapping", "scp_codes", "diagnostic_class", "diagnostic_subclass"]):
        role = "mapping_file" if "mapping" in rel_lower else "label_or_diagnostic_statement"
        return role, False, LEAKAGE_EXCLUSION_MESSAGE
    if rel_lower.startswith("features/") and name_lower == "feature_description.csv":
        return "metadata_or_description", False, "Feature description metadata is not a per-record model input table."
    if rel_lower.startswith("features/"):
        return "unknown", False, "Feature-like location but not one of the explicitly allowed Stage 3 feature tables."
    if rel_lower.startswith("median_beats/") or rel_lower.startswith("fiducial_points/"):
        return "waveform_or_fiducial_related", False, "Waveform or fiducial related files are not selected as structured tabular input in Stage 3."
    if name_lower in {"records", "license.txt", "sha256sums.txt"}:
        return "metadata_or_description", False, "Dataset metadata file is not a per-record structured feature table."
    return "unknown", False, "Not an explicitly allowed PTB-XL+ structured feature table."


def score_candidate(path: Path, metadata_ids: set[str] | None = None, nrows: int = 5000) -> dict[str, Any]:
    """Backward-compatible wrapper for older Stage 2 tests.

    Stage 3 validation uses `inspect_candidate(path, ptbxl_plus_root, ...)` so
    official relative paths can be role-classified. This wrapper keeps the old
    function importable without changing the leakage-safe validator behavior.
    """
    root = path.parent.parent if path.parent.name in {"features", "labels"} else path.parent
    row = inspect_candidate(path, root, metadata_ids=metadata_ids, nrows=nrows)
    if row["role"] == "unknown" and any(token in path.name.lower() for token in ["ecgdeli_features", "12sl_features", "unig_features"]):
        row["allowed_as_structured_input"] = True
        row["excluded"] = False
        row["exclude_reason"] = ""
        row["score"] = max(int(row["score"]), 80)
    return row


def find_candidate_files(ptbxl_plus_root: Path) -> list[Path]:
    if not ptbxl_plus_root.exists():
        return []
    files: list[Path] = []
    for suffix in FEATURE_SUFFIXES:
        files.extend(ptbxl_plus_root.rglob(f"*{suffix}"))
    return sorted(set(path for path in files if path.is_file()))


def inspect_candidate(path: Path, ptbxl_plus_root: Path, metadata_ids: set[str] | None = None, nrows: int = 5000) -> dict[str, Any]:
    relative_path = _normalise_rel(path, ptbxl_plus_root)
    role, allowed, role_reason = classify_file_role(path, ptbxl_plus_root)
    row: dict[str, Any] = {
        "candidate_path": str(path),
        "relative_path": relative_path,
        "file_type": path.suffix.lower().lstrip("."),
        "role": role,
        "allowed_as_structured_input": bool(allowed),
        "excluded": not bool(allowed),
        "exclude_reason": "" if allowed else role_reason,
        "n_rows": 0,
        "n_columns": 0,
        "id_column": "",
        "numeric_columns": 0,
        "non_numeric_columns": 0,
        "ecg_feature_keyword_count": 0,
        "label_leakage_keyword_count": 0,
        "aligned_preview_rows": 0,
        "score": 0,
        "selected": False,
        "error": "",
    }
    try:
        df = read_table_auto(path, nrows=nrows)
    except Exception as exc:
        row["excluded"] = True
        row["exclude_reason"] = f"read failed: {exc}"
        row["error"] = str(exc)
        return row

    row["n_rows"] = int(len(df))
    row["n_columns"] = int(len(df.columns))
    id_col = identify_id_column([str(col) for col in df.columns])
    row["id_column"] = id_col
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    row["numeric_columns"] = len(numeric_cols)
    row["non_numeric_columns"] = len(df.columns) - len(numeric_cols)
    row["ecg_feature_keyword_count"] = int(sum(1 for kw in ECG_FEATURE_KEYWORDS if any(kw in str(col).lower() for col in df.columns)))
    row["label_leakage_keyword_count"] = int(sum(1 for kw in LABEL_LEAKAGE_KEYWORDS if any(kw in str(col).lower() for col in df.columns) or kw in relative_path.lower()))
    if id_col and metadata_ids:
        row["aligned_preview_rows"] = int(_normalise_id_series(df[id_col]).isin(metadata_ids).sum())

    score = 0
    score += ALLOWED_FEATURE_FILES.get(relative_path.lower(), 0)
    if row["n_rows"] > 1000:
        score += 25
    if row["n_columns"] > 20:
        score += 25
    if id_col:
        score += 30
    if row["numeric_columns"] > 20:
        score += 20
    if row["ecg_feature_keyword_count"] > 0:
        score += 10 + min(int(row["ecg_feature_keyword_count"]), 5) * 5
    if row["aligned_preview_rows"] > 0:
        score += 30
    if row["label_leakage_keyword_count"] > 0 and not allowed:
        score = 0
    row["score"] = int(score)

    if allowed:
        blockers = []
        if not id_col:
            blockers.append("missing supported ID column")
        if row["n_rows"] <= 1000:
            blockers.append("n_rows <= 1000 in preview")
        if row["n_columns"] <= 20:
            blockers.append("n_columns <= 20")
        if row["numeric_columns"] <= 20:
            blockers.append("numeric_columns <= 20")
        if blockers:
            row["excluded"] = True
            row["exclude_reason"] = "; ".join(blockers)
    return row


def _load_metadata_ids(config: dict[str, Any], root: Path) -> set[str] | None:
    metadata_path = resolve_path(config.get("ptbxl", {}).get("metadata_csv"), root)
    if metadata_path is None or not metadata_path.exists():
        return None
    df = pd.read_csv(metadata_path, usecols=["ecg_id"])
    return set(_normalise_id_series(df["ecg_id"]))


def select_candidate(file_roles: pd.DataFrame) -> dict[str, Any] | None:
    if file_roles.empty:
        return None
    eligible = file_roles[
        file_roles["allowed_as_structured_input"].eq(True)
        & file_roles["excluded"].eq(False)
        & file_roles["relative_path"].isin(ALLOWED_FEATURE_FILES)
    ].copy()
    if eligible.empty:
        return None
    eligible["priority"] = eligible["relative_path"].map(ALLOWED_FEATURE_FILES)
    eligible = eligible.sort_values(["priority", "score"], ascending=[False, False])
    return eligible.iloc[0].to_dict()


def _report(ptbxl_plus_root: Path, file_roles: pd.DataFrame, selected: dict[str, Any] | None, blocking: str) -> str:
    roles_md = file_roles.to_markdown(index=False) if not file_roles.empty else "No candidate files found."
    selected_text = "none" if selected is None else str(selected["candidate_path"])
    id_text = "none" if selected is None else str(selected.get("id_column") or "none")
    allowed = []
    excluded = []
    high_risk = []
    if not file_roles.empty:
        allowed = file_roles[file_roles["allowed_as_structured_input"].eq(True)]["relative_path"].tolist()
        excluded = file_roles[file_roles["excluded"].eq(True)]["relative_path"].tolist()
        high_risk = file_roles[file_roles["role"].isin(["label_or_diagnostic_statement", "mapping_file"])]["relative_path"].tolist()
    return f"""# PTB-XL+ Validation Report

## 1. Search Scope

- {ptbxl_plus_root}

## 2. Candidate Files

{roles_md}

## 3. Selected Feature File

{selected_text}

## 4. ID Column Detection

{id_text}

## 5. Feature Type Summary

- allowed feature files: {", ".join(allowed) if allowed else "none"}
- excluded files: {", ".join(excluded) if excluded else "none"}
- high leakage risk files: {", ".join(high_risk) if high_risk else "none"}

## 6. Missingness Summary

Missingness is audited during alignment after full selected-file loading.

## 7. Alignment Readiness

{"ready for alignment" if selected is not None and not blocking else "not ready"}

## 8. Blocking Issue

{blocking or "none"}

## 9. Recommended Next Action

{"Run `bash scripts/01c_align_ptbxl_plus.sh`." if selected is not None and not blocking else "PTB-XL+ files are still missing. Please download/extract PTB-XL+ into `data/raw/ptbxl_plus/` so that `data/raw/ptbxl_plus/features/ecgdeli_features.csv` exists."}
"""


def validate(config_path: str | Path = "configs/data_ptbxl.yaml") -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    ptbxl_plus_root = resolve_path(config.get("ptbxl_plus", {}).get("features_path", "data/raw/ptbxl_plus"), root)
    results_dir = ensure_dir(resolve_path(config.get("output", {}).get("results_dir", "results"), root))
    metadata_ids = _load_metadata_ids(config, root)
    files = find_candidate_files(ptbxl_plus_root)
    rows = [inspect_candidate(path, ptbxl_plus_root, metadata_ids=metadata_ids) for path in files]
    file_roles = pd.DataFrame(rows)
    selected = select_candidate(file_roles)
    if selected is not None:
        file_roles.loc[file_roles["candidate_path"].eq(selected["candidate_path"]), "selected"] = True
        blocking = ""
    else:
        blocking = MISSING_MESSAGE if file_roles.empty else "No leakage-safe PTB-XL+ feature table passed validation. " + MISSING_MESSAGE

    expected_cols = [
        "candidate_path",
        "relative_path",
        "file_type",
        "role",
        "allowed_as_structured_input",
        "excluded",
        "exclude_reason",
        "n_rows",
        "n_columns",
        "id_column",
        "numeric_columns",
        "non_numeric_columns",
        "ecg_feature_keyword_count",
        "label_leakage_keyword_count",
        "score",
        "selected",
    ]
    if file_roles.empty:
        file_roles = pd.DataFrame(columns=expected_cols + ["aligned_preview_rows", "error"])
    safe_to_csv(file_roles, results_dir / "ptbxl_plus_file_roles.csv")
    safe_to_csv(file_roles[expected_cols], results_dir / "ptbxl_plus_candidates.csv")
    write_markdown(results_dir / "ptbxl_plus_validation_report.md", _report(ptbxl_plus_root, file_roles, selected, blocking))
    print("PTB-XL+ validation completed.")
    print(f"Selected feature file: {selected['candidate_path'] if selected else 'none'}")
    print(f"Blocking issue: {blocking or 'none'}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate PTB-XL+ structured feature candidates with leakage-safe role classification.")
    parser.add_argument("--config", default="configs/data_ptbxl.yaml")
    args = parser.parse_args()
    raise SystemExit(validate(args.config))


if __name__ == "__main__":
    main()
