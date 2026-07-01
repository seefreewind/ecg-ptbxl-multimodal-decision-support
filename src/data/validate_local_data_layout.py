from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, load_yaml, project_root_from_config, read_table_auto, resolve_path, safe_to_csv, write_markdown

PTBXL_REQUIRED_COLUMNS = ["ecg_id", "filename_lr", "filename_hr", "scp_codes", "strat_fold"]
SCP_EXPECTED_COLUMNS = ["diagnostic", "diagnostic_class", "diagnostic_subclass"]
FEATURE_SUFFIXES = [".csv", ".tsv", ".parquet", ".feather", ".pkl", ".pickle"]
ID_CANDIDATES = ["ecg_id", "record_id", "id", "ECG_ID"]
ECG_KEYWORDS = ["qrs", "qt", "qtc", "pr", "rr", "axis", "amplitude", "duration", "interval", "rate"]
PTBXL_PLUS_PATH_KEYWORDS = ["ptbxl", "ptb-xl", "ptbxl_plus", "ptb-xl-plus", "ecgdeli", "unig", "features"]
UNRELATED_PATTERNS = ["confirmed_pair_structured_audit_packet", "structured_audit_no_duplicate_review_statement", "structured_audit", "adc_safety_lifecycle", "zenodo_deposit"]


def _paths(config: dict[str, Any], root: Path) -> dict[str, Path]:
    output = config.get("output", {})
    return {
        "ptbxl_dir": root / "data" / "raw" / "ptbxl",
        "ptbxl_plus_dir": root / "data" / "raw" / "ptbxl_plus",
        "results_dir": resolve_path(output.get("results_dir", "results"), root),
    }


def _read_csv_preview(path: Path, nrows: int = 5) -> tuple[bool, list[str], int | None, str]:
    try:
        preview = pd.read_csv(path, nrows=nrows)
        return True, list(preview.columns), len(preview), ""
    except Exception as exc:
        return False, [], None, str(exc)


def _record_base_exists(record_base: Path) -> bool:
    return record_base.exists() or (record_base.with_suffix(".hea").exists() and record_base.with_suffix(".dat").exists())


def _sample_waveform_check(ptbxl_dir: Path, metadata_path: Path | None) -> dict[str, Any]:
    info = {
        "filename_lr_checked": 0,
        "filename_lr_found": 0,
        "filename_lr_missing": 0,
        "missing_examples": [],
        "wfdb_installed": importlib.util.find_spec("wfdb") is not None,
        "wfdb_status": "warning",
        "wfdb_message": "wfdb not installed. Please run: pip install wfdb",
    }
    if metadata_path is None or not metadata_path.exists():
        info["wfdb_message"] = "metadata missing; filename_lr waveform references were not checked"
        return info
    try:
        df = pd.read_csv(metadata_path, nrows=20)
    except Exception as exc:
        info["wfdb_message"] = f"metadata preview read failed: {exc}"
        return info
    if "filename_lr" not in df.columns:
        info["wfdb_message"] = "filename_lr column missing; waveform references were not checked"
        return info
    first_existing: Path | None = None
    for rel in df["filename_lr"].dropna().head(20):
        info["filename_lr_checked"] += 1
        rel_text = str(rel).strip()
        record_base = ptbxl_dir / rel_text
        if rel_text.endswith(".hea") or rel_text.endswith(".dat"):
            record_base = ptbxl_dir / rel_text.rsplit(".", 1)[0]
        if _record_base_exists(record_base):
            info["filename_lr_found"] += 1
            if first_existing is None:
                first_existing = record_base
        else:
            info["filename_lr_missing"] += 1
            if len(info["missing_examples"]) < 5:
                info["missing_examples"].append(str(record_base))
    if info["wfdb_installed"] and first_existing is not None:
        try:
            import wfdb  # type: ignore

            wfdb.rdsamp(str(first_existing))
            info["wfdb_status"] = "success"
            info["wfdb_message"] = f"wfdb.rdsamp succeeded for {first_existing}"
        except Exception as exc:
            info["wfdb_status"] = "warning"
            info["wfdb_message"] = f"wfdb installed but sample loading failed: {exc}"
    return info


def _count_waveform_files(records100: Path) -> dict[str, Any]:
    if not records100.exists():
        return {"records100_exists": False, "hea_count_preview": 0, "dat_count_preview": 0}
    hea = []
    dat = []
    for path in records100.rglob("*.hea"):
        hea.append(path)
        if len(hea) >= 20:
            break
    for path in records100.rglob("*.dat"):
        dat.append(path)
        if len(dat) >= 20:
            break
    return {"records100_exists": True, "hea_count_preview": len(hea), "dat_count_preview": len(dat)}


def _has_id_column(columns: list[str]) -> str:
    lower_map = {str(c).lower(): str(c) for c in columns}
    for col in ID_CANDIDATES:
        if col.lower() in lower_map:
            return lower_map[col.lower()]
    return ""


def _is_unrelated(path: Path) -> str:
    lower_path = str(path).lower()
    for pattern in UNRELATED_PATTERNS:
        if pattern in lower_path:
            return pattern
    return ""


def _inspect_ptbxl_plus_file(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "candidate_path": str(path),
        "file_type": path.suffix.lower().lstrip("."),
        "readable": False,
        "n_rows_if_readable": 0,
        "n_columns_if_readable": 0,
        "id_column_found": "",
        "criteria_met": 0,
        "accepted": False,
        "excluded": False,
        "exclude_reason": "",
        "reason": "",
    }
    unrelated = _is_unrelated(path)
    if unrelated:
        row.update({"excluded": True, "exclude_reason": f"unrelated path pattern: {unrelated}", "reason": "explicitly excluded unrelated structured/audit file"})
        return row
    lower_path = str(path).lower()
    path_keyword = any(k in lower_path for k in PTBXL_PLUS_PATH_KEYWORDS)
    try:
        df = read_table_auto(path)
        row["readable"] = True
        row["n_rows_if_readable"] = int(len(df))
        row["n_columns_if_readable"] = int(len(df.columns))
        columns = [str(c) for c in df.columns]
        id_col = _has_id_column(columns)
        row["id_column_found"] = id_col
        ecg_keyword_hits = sorted({kw for kw in ECG_KEYWORDS if any(kw in str(c).lower() for c in columns)})
        criteria = [
            path_keyword,
            bool(id_col),
            len(df.columns) > 20,
            bool(ecg_keyword_hits),
            len(df) > 1000,
        ]
        row["criteria_met"] = int(sum(criteria))
        row["accepted"] = row["criteria_met"] >= 2 and bool(id_col) and len(df) >= 1000
        if not row["accepted"]:
            row["excluded"] = True
            reasons = []
            if len(df) < 1000:
                reasons.append("rows < 1000")
            if not id_col:
                reasons.append("missing supported ID column")
            if row["criteria_met"] < 2:
                reasons.append("fewer than two PTB-XL+ criteria met")
            row["exclude_reason"] = "; ".join(reasons) or "did not pass PTB-XL+ filter"
        row["reason"] = f"path_keyword={path_keyword}; ecg_keywords={','.join(ecg_keyword_hits) or 'none'}"
    except Exception as exc:
        row.update({"excluded": True, "exclude_reason": f"read failed: {exc}", "reason": "read failed"})
    return row


def _ptbxl_plus_candidates(ptbxl_plus_dir: Path) -> list[dict[str, Any]]:
    if not ptbxl_plus_dir.exists():
        return []
    files = []
    for suffix in FEATURE_SUFFIXES:
        files.extend(ptbxl_plus_dir.rglob(f"*{suffix}"))
    return [_inspect_ptbxl_plus_file(path) for path in sorted(set(files))]


def _status(found: bool, required: bool = True) -> str:
    if found:
        return "success"
    return "failed" if required else "partial"


def _build_report(rows: list[dict[str, Any]], plus_rows: list[dict[str, Any]], waveform_info: dict[str, Any], blocking: list[str], recommended_action: str) -> str:
    summary_df = pd.DataFrame(rows)
    plus_df = pd.DataFrame(plus_rows)
    required_md = summary_df[summary_df["section"].eq("required_file")].to_markdown(index=False) if not summary_df.empty else "No checks recorded."
    waveform_md = summary_df[summary_df["section"].eq("waveform")].to_markdown(index=False) if not summary_df.empty else "No waveform checks recorded."
    plus_md = plus_df.to_markdown(index=False) if not plus_df.empty else "No PTB-XL+ candidates found under data/raw/ptbxl_plus/."
    blocking_text = "\n".join(f"- {item}" for item in blocking) if blocking else "- None"
    return f"""# Local Data Layout Report

## 1. Required PTB-XL Files

{required_md}

## 2. Waveform Directory Check

{waveform_md}

## 3. Sample WFDB File Check

- filename_lr checked: {waveform_info.get('filename_lr_checked', 0)}
- filename_lr found: {waveform_info.get('filename_lr_found', 0)}
- filename_lr missing: {waveform_info.get('filename_lr_missing', 0)}
- missing examples: {', '.join(waveform_info.get('missing_examples', [])) or 'none'}
- wfdb installed: {'yes' if waveform_info.get('wfdb_installed') else 'no'}
- wfdb status: {waveform_info.get('wfdb_status')}
- wfdb message: {waveform_info.get('wfdb_message')}

## 4. PTB-XL+ Directory Check

{plus_md}

## 5. Blocking Issues

{blocking_text}

## 6. Recommended User Action

{recommended_action}
"""


def validate(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    paths = _paths(config, root)
    results_dir = ensure_dir(paths["results_dir"])
    ptbxl_dir = paths["ptbxl_dir"]
    plus_dir = paths["ptbxl_plus_dir"]

    metadata_path = ptbxl_dir / "ptbxl_database.csv"
    scp_path = ptbxl_dir / "scp_statements.csv"
    records100 = ptbxl_dir / "records100"
    records500 = ptbxl_dir / "records500"

    rows: list[dict[str, Any]] = []
    blocking: list[str] = []

    for label, path, required in [
        ("ptbxl_database.csv", metadata_path, True),
        ("scp_statements.csv", scp_path, True),
        ("records100", records100, True),
        ("records500", records500, False),
    ]:
        exists = path.exists()
        rows.append({"section": "required_file", "item": label, "path": str(path), "exists": exists, "required": required, "status": _status(exists, required)})
        if required and not exists:
            blocking.append(f"Missing required PTB-XL item: {path}")

    if metadata_path.exists():
        ok, columns, preview_rows, err = _read_csv_preview(metadata_path)
        missing_cols = [c for c in PTBXL_REQUIRED_COLUMNS if c not in columns]
        rows.append({"section": "required_file", "item": "ptbxl_database.csv columns", "path": str(metadata_path), "exists": ok, "required": True, "status": "success" if ok and not missing_cols else "failed", "detail": f"columns={columns}; missing={missing_cols}; error={err}"})
        if missing_cols:
            blocking.append(f"ptbxl_database.csv missing columns: {missing_cols}")
    if scp_path.exists():
        ok, columns, preview_rows, err = _read_csv_preview(scp_path)
        has_mapping_column = any(c in columns for c in SCP_EXPECTED_COLUMNS)
        rows.append({"section": "required_file", "item": "scp_statements.csv columns", "path": str(scp_path), "exists": ok, "required": True, "status": "success" if ok and has_mapping_column else "failed", "detail": f"columns={columns}; expected_any={SCP_EXPECTED_COLUMNS}; error={err}"})
        if not has_mapping_column:
            blocking.append("scp_statements.csv lacks diagnostic / diagnostic_class / diagnostic_subclass columns in preview")

    wf_counts = _count_waveform_files(records100)
    rows.append({"section": "waveform", "item": "records100 .hea preview count", "path": str(records100), "exists": wf_counts["records100_exists"], "required": True, "status": "success" if wf_counts["hea_count_preview"] > 0 else "failed", "detail": wf_counts["hea_count_preview"]})
    rows.append({"section": "waveform", "item": "records100 .dat preview count", "path": str(records100), "exists": wf_counts["records100_exists"], "required": True, "status": "success" if wf_counts["dat_count_preview"] > 0 else "failed", "detail": wf_counts["dat_count_preview"]})
    if records100.exists() and (wf_counts["hea_count_preview"] == 0 or wf_counts["dat_count_preview"] == 0):
        blocking.append("records100 exists but no .hea/.dat files were found in the first recursive preview")

    waveform_info = _sample_waveform_check(ptbxl_dir, metadata_path if metadata_path.exists() else None)
    if metadata_path.exists() and waveform_info["filename_lr_checked"] > 0 and waveform_info["filename_lr_found"] == 0:
        blocking.append("filename_lr paths from metadata did not resolve to WFDB .hea/.dat files under data/raw/ptbxl")

    plus_rows = _ptbxl_plus_candidates(plus_dir)
    plus_dir_exists = plus_dir.exists()
    rows.append({"section": "ptbxl_plus", "item": "ptbxl_plus directory", "path": str(plus_dir), "exists": plus_dir_exists, "required": False, "status": "partial" if not plus_dir_exists else "success"})
    accepted_plus = [r for r in plus_rows if r.get("accepted")]

    if blocking:
        recommended_action = "Place PTB-XL files under data/raw/ptbxl/ as described in docs/DATA_SETUP.md, then rerun the validation and Stage 0 commands."
        exit_code = 1
    else:
        recommended_action = "Run data path discovery and Stage 0/1 preparation commands."
        exit_code = 0
    if plus_dir_exists and not accepted_plus:
        recommended_action += " PTB-XL+ is optional; if multimodal modeling is required, place valid PTB-XL+ feature files under data/raw/ptbxl_plus/."

    summary_df = pd.DataFrame(rows)
    safe_to_csv(summary_df, results_dir / "local_data_layout_summary.csv")
    report = _build_report(rows, plus_rows, waveform_info, blocking, recommended_action)
    write_markdown(results_dir / "local_data_layout_report.md", report)

    print("Local data layout validation completed.")
    print(f"PTB-XL metadata: {'found' if metadata_path.exists() else 'missing'}")
    print(f"SCP statements: {'found' if scp_path.exists() else 'missing'}")
    print(f"records100: {'found' if records100.exists() else 'missing'}")
    print(f"records500: {'found' if records500.exists() else 'optional missing'}")
    print(f"PTB-XL+ candidate: {'found' if accepted_plus else 'missing'}")
    print(f"Report: {results_dir / 'local_data_layout_report.md'}")
    return exit_code


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate local PTB-XL/PTB-XL+ raw data layout quickly.")
    parser.add_argument("--config", default="configs/data_ptbxl.yaml", help="Path to configs/data_ptbxl.yaml")
    args = parser.parse_args()
    raise SystemExit(validate(args.config))


if __name__ == "__main__":
    main()
