from __future__ import annotations

import argparse
import importlib.util
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.utils.io import ensure_dir, load_yaml, project_root_from_config, read_table_auto, resolve_path, safe_to_csv, write_markdown

ID_CANDIDATES = ["ecg_id", "record_id", "id", "ECG_ID"]
ECG_FEATURE_KEYWORDS = ["age", "sex", "qrs", "qt", "qtc", "pr", "rr", "axis", "amplitude", "duration", "interval", "rate"]
PLUS_KEYWORDS = ["ptbxl_plus", "ptb-xl-plus", "ptbxlplus", "features", "ecgdeli", "unig", "structured"]
UNRELATED_PATTERNS = ["adc_safety_lifecycle", "zenodo_deposit", "confirmed_pair_structured_audit_packet", "structured_audit"]
FEATURE_SUFFIXES = [".csv", ".tsv", ".parquet", ".feather", ".pkl", ".pickle"]
METADATA_REQUIRED_COLUMNS = ["ecg_id", "scp_codes", "strat_fold", "filename_lr"]
EXCLUDED_FEATURE_FILENAMES = {
    "ptbxl_database.csv",
    "scp_statements.csv",
    "ptbxl_labels.csv",
    "ptbxl_train.csv",
    "ptbxl_val.csv",
    "ptbxl_test.csv",
}


def _unique_existing(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen = set()
    for path in paths:
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            continue
        if resolved.exists() and resolved not in seen:
            seen.add(resolved)
            out.append(resolved)
    return out


def search_roots(project_root: Path) -> list[Path]:
    return _unique_existing(
        [
            project_root,
            project_root / "data",
            project_root / "data" / "raw",
            project_root.parent,
            project_root.parent.parent,
        ]
    )


def _path_contains(path: Path, text: str) -> bool:
    return text.lower() in str(path).lower()


def _read_csv_head(path: Path, nrows: int = 50) -> tuple[bool, pd.DataFrame | None, str]:
    try:
        return True, pd.read_csv(path, nrows=nrows), ""
    except Exception as exc:
        return False, None, str(exc)


def _metadata_score(path: Path, project_root: Path) -> tuple[int, str, dict[str, Any]]:
    score = 0
    reasons: list[str] = []
    info: dict[str, Any] = {"readable": False, "columns_found": [], "file_size": path.stat().st_size if path.exists() else 0}
    preferred = (project_root / "data" / "raw" / "ptbxl" / "ptbxl_database.csv").resolve()
    if path.resolve() == preferred:
        score += 100
        reasons.append("preferred default path")
    if _path_contains(path.parent, "ptbxl") or _path_contains(path.parent, "ptb-xl"):
        score += 40
        reasons.append("path contains ptbxl/ptb-xl")
    ok, df, err = _read_csv_head(path)
    info["readable"] = ok
    if ok and df is not None:
        found = [c for c in METADATA_REQUIRED_COLUMNS if c in df.columns]
        info["columns_found"] = found
        score += len(found) * 25
        if set(METADATA_REQUIRED_COLUMNS).issubset(df.columns):
            score += 80
            reasons.append("contains required PTB-XL metadata columns")
        if "filename_hr" in df.columns:
            score += 10
            reasons.append("contains filename_hr")
    else:
        reasons.append(f"read failed: {err}")
    if 10_000 <= info["file_size"] <= 200_000_000:
        score += 10
        reasons.append("file size is plausible")
    return score, "; ".join(reasons), info


def _scp_score(path: Path, metadata_path: Path | None, project_root: Path) -> tuple[int, str, dict[str, Any]]:
    score = 0
    reasons: list[str] = []
    info: dict[str, Any] = {"readable": False, "columns_found": [], "file_size": path.stat().st_size if path.exists() else 0}
    if metadata_path is not None:
        try:
            if path.parent.resolve() == metadata_path.parent.resolve():
                score += 80
                reasons.append("same directory as selected metadata")
            elif path.parent.parent.resolve() == metadata_path.parent.resolve() or path.parent.resolve() == metadata_path.parent.parent.resolve():
                score += 30
                reasons.append("adjacent to selected metadata")
        except Exception:
            pass
    preferred = (project_root / "data" / "raw" / "ptbxl" / "scp_statements.csv").resolve()
    if path.resolve() == preferred:
        score += 100
        reasons.append("preferred default path")
    if _path_contains(path.parent, "ptbxl") or _path_contains(path.parent, "ptb-xl"):
        score += 30
        reasons.append("path contains ptbxl/ptb-xl")
    ok, df, err = _read_csv_head(path)
    info["readable"] = ok
    if ok and df is not None:
        info["columns_found"] = list(df.columns)
        if "diagnostic_class" in df.columns:
            score += 80
            reasons.append("contains diagnostic_class")
        if "diagnostic" in df.columns:
            score += 20
            reasons.append("contains diagnostic flag")
    else:
        reasons.append(f"read failed: {err}")
    return score, "; ".join(reasons), info


def _find_named_files(roots: list[Path], filename: str) -> list[Path]:
    matches: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        try:
            matches.extend(root.rglob(filename))
        except (PermissionError, OSError):
            continue
    return sorted(set(p.resolve() for p in matches if p.is_file()))


def _normalise_record_base(base_dir: Path, rel_record: str) -> Path:
    rel = str(rel_record).strip()
    if rel.endswith(".hea") or rel.endswith(".dat"):
        rel = rel.rsplit(".", 1)[0]
    return base_dir / rel


def _record_exists(record_base: Path) -> bool:
    if record_base.exists():
        return True
    return record_base.with_suffix(".hea").exists() and record_base.with_suffix(".dat").exists()


def _waveform_base_candidates(metadata_path: Path, project_root: Path) -> list[Path]:
    meta_dir = metadata_path.parent
    return _unique_existing(
        [
            meta_dir,
            meta_dir / "records100",
            meta_dir / "records500",
            project_root / "data" / "raw" / "ptbxl",
            project_root / "data" / "raw" / "ptbxl" / "records100",
            project_root / "data" / "raw" / "ptbxl" / "records500",
        ]
    )


def _check_waveform_bases(metadata_path: Path, project_root: Path) -> tuple[Path | None, pd.DataFrame, dict[str, Any]]:
    df = pd.read_csv(metadata_path, nrows=20)
    rows: list[dict[str, Any]] = []
    best_path: Path | None = None
    best_found = -1
    for base in _waveform_base_candidates(metadata_path, project_root):
        for col in ["filename_lr", "filename_hr"]:
            if col not in df.columns:
                continue
            checked = 0
            found = 0
            missing_examples: list[str] = []
            for rel in df[col].dropna().head(20):
                checked += 1
                record_base = _normalise_record_base(base, str(rel))
                if _record_exists(record_base):
                    found += 1
                elif len(missing_examples) < 3:
                    missing_examples.append(str(record_base))
            rows.append(
                {
                    "candidate_path": str(base),
                    "candidate_type": "waveform_base",
                    "file_type": "directory",
                    "n_rows_if_readable": checked,
                    "n_columns_if_readable": "",
                    "id_column_found": "",
                    "score": found,
                    "reason": f"column={col}; found={found}/{checked}; missing_examples={'; '.join(missing_examples)}",
                }
            )
            if col == "filename_lr" and found > best_found:
                best_found = found
                best_path = base
    wfdb_installed = importlib.util.find_spec("wfdb") is not None
    wfdb_message = "wfdb is not installed. File existence check was performed, but waveform loading was not validated."
    if wfdb_installed and best_path is not None and best_found > 0 and "filename_lr" in df.columns:
        try:
            import wfdb  # type: ignore

            for rel in df["filename_lr"].dropna().head(20):
                record_base = _normalise_record_base(best_path, str(rel))
                if _record_exists(record_base):
                    wfdb.rdsamp(str(record_base))
                    wfdb_message = f"wfdb.rdsamp succeeded for {record_base}"
                    break
        except Exception as exc:
            wfdb_message = f"wfdb is installed but waveform loading failed: {exc}"
    info = {"best_found": best_found, "wfdb_installed": wfdb_installed, "wfdb_message": wfdb_message}
    return best_path if best_found > 0 else None, pd.DataFrame(rows), info


def _feature_score(path: Path, project_root: Path, metadata_ids: set[str] | None = None) -> tuple[int, str, dict[str, Any]]:
    score = 0
    reasons: list[str] = []
    info: dict[str, Any] = {
        "readable": False,
        "n_rows": 0,
        "n_columns": 0,
        "id_column": "",
        "feature_keyword_hits": [],
        "aligned_preview": 0,
        "excluded": False,
        "exclude_reason": "",
    }
    lower_path = str(path).lower()
    generated_dirs = [
        project_root / "results",
        project_root / "tables",
        project_root / "data" / "processed",
        project_root / "data" / "splits",
    ]
    for generated_dir in generated_dirs:
        try:
            if path.resolve().is_relative_to(generated_dir.resolve()):
                info["excluded"] = True
                info["exclude_reason"] = "generated project outputs are not raw PTB-XL+ features"
                return 0, "excluded: " + info["exclude_reason"], info
        except FileNotFoundError:
            continue
    if path.name.lower() in EXCLUDED_FEATURE_FILENAMES:
        info["excluded"] = True
        info["exclude_reason"] = f"core PTB-XL file is not PTB-XL+ structured features: {path.name}"
        return 0, "excluded: " + info["exclude_reason"], info
    for pattern in UNRELATED_PATTERNS:
        if pattern in lower_path:
            info["excluded"] = True
            info["exclude_reason"] = f"unrelated path pattern: {pattern}"
            return 0, "excluded: " + info["exclude_reason"], info
    keyword_hits = [keyword for keyword in PLUS_KEYWORDS if keyword in lower_path]
    if not keyword_hits:
        info["excluded"] = True
        info["exclude_reason"] = "path does not contain PTB-XL+ feature keywords"
        return 0, "excluded: " + info["exclude_reason"], info
    for keyword in keyword_hits:
        score += 20
        reasons.append(f"keyword:{keyword}")
    try:
        df = read_table_auto(path, nrows=2000)
        info["readable"] = True
        info["n_rows"] = len(df)
        info["n_columns"] = len(df.columns)
        lower_cols = {str(c).lower(): c for c in df.columns}
        id_col = ""
        for candidate in ID_CANDIDATES:
            if candidate.lower() in lower_cols:
                id_col = str(lower_cols[candidate.lower()])
                break
        info["id_column"] = id_col
        if id_col:
            score += 60
            reasons.append(f"id column:{id_col}")
            if metadata_ids:
                aligned = df[id_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).isin(metadata_ids).sum()
                info["aligned_preview"] = int(aligned)
                if aligned > 0:
                    score += 80
                    reasons.append(f"preview aligns with PTB-XL ids:{aligned}")
        hits = sorted({kw for kw in ECG_FEATURE_KEYWORDS if any(kw in str(c).lower() for c in df.columns)})
        info["feature_keyword_hits"] = hits
        if hits:
            score += len(hits) * 10
            reasons.append("ECG feature keywords:" + ",".join(hits))
        if len(df.columns) > 20:
            score += 20
            reasons.append("columns > 20")
        if len(df) > 1000:
            score += 30
            reasons.append("rows > 1000 in preview/read")
        if len(df) < 1000:
            info["excluded"] = True
            info["exclude_reason"] = "rows < 1000"
        elif not id_col:
            info["excluded"] = True
            info["exclude_reason"] = "missing supported ID column"
        if info["excluded"]:
            return score, "; ".join(reasons + ["excluded: " + info["exclude_reason"]]), info
    except Exception as exc:
        info["excluded"] = True
        info["exclude_reason"] = f"read failed:{exc}"
        reasons.append(info["exclude_reason"])
    return score, "; ".join(reasons), info


def _find_feature_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        try:
            for suffix in FEATURE_SUFFIXES:
                files.extend(root.rglob(f"*{suffix}"))
        except (PermissionError, OSError):
            continue
    return sorted(set(p.resolve() for p in files if p.is_file()))


def _relative_or_absolute(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _update_config(
    config_path: Path,
    project_root: Path,
    metadata_path: Path | None,
    scp_path: Path | None,
    records_base_dir: Path | None,
    selected_plus: Path | None,
    multiple_plus_candidates: bool,
) -> tuple[bool, str]:
    if metadata_path is None or scp_path is None:
        return False, "Config was not updated because PTB-XL metadata and/or scp_statements were not found."
    config = load_yaml(config_path)
    backup_path = config_path.with_suffix(config_path.suffix + ".bak")
    shutil.copy2(config_path, backup_path)
    config.setdefault("ptbxl", {})
    config["ptbxl"].update(
        {
            "metadata_csv": _relative_or_absolute(metadata_path, project_root),
            "scp_statements_csv": _relative_or_absolute(scp_path, project_root),
            "records_base_dir": _relative_or_absolute(records_base_dir or metadata_path.parent, project_root),
            "sampling_rate": 100,
            "waveform_column_100hz": "filename_lr",
            "waveform_column_500hz": "filename_hr",
        }
    )
    config.setdefault("ptbxl_plus", {})
    if selected_plus is not None:
        config["ptbxl_plus"]["features_path"] = _relative_or_absolute(selected_plus.parent if selected_plus.is_file() else selected_plus, project_root)
        config["ptbxl_plus"]["features_csv"] = None if multiple_plus_candidates else _relative_or_absolute(selected_plus, project_root)
    else:
        config["ptbxl_plus"]["features_path"] = "data/raw/ptbxl_plus"
        config["ptbxl_plus"]["features_csv"] = None
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)
    return True, f"Config updated. Backup saved to {backup_path}."


def _report(
    roots: list[Path],
    metadata_rows: list[dict[str, Any]],
    scp_rows: list[dict[str, Any]],
    waveform_rows: pd.DataFrame,
    plus_rows: list[dict[str, Any]],
    config_message: str,
    blocking_issue: str,
    user_action: str,
) -> str:
    def table(rows):
        df = pd.DataFrame(rows)
        return df.to_markdown(index=False) if not df.empty else "No candidates found."

    waveform_md = waveform_rows.to_markdown(index=False) if not waveform_rows.empty else "No waveform base candidates checked."
    return f"""# Data Path Discovery Report

## 1. Search Scope

{chr(10).join(f'- {root}' for root in roots)}

## 2. PTB-XL Metadata Candidates

{table(metadata_rows)}

## 3. SCP Statements Candidates

{table(scp_rows)}

## 4. Waveform Base Directory Check

{waveform_md}

## 5. PTB-XL+ Structured Feature Candidates

{table(plus_rows)}

## 6. Config Update Result

{config_message}

## 7. Current Blocking Issue

{blocking_issue}

## 8. Recommended User Action

{user_action}
"""


def discover(config_path: str | Path) -> int:
    config_path = Path(config_path)
    project_root = project_root_from_config(config_path)
    config = load_yaml(config_path) if config_path.exists() else {}
    results_dir = ensure_dir(resolve_path(config.get("output", {}).get("results_dir", "results"), project_root))
    roots = search_roots(project_root)

    metadata_candidates = _find_named_files(roots, "ptbxl_database.csv")
    metadata_rows: list[dict[str, Any]] = []
    for path in metadata_candidates:
        score, reason, info = _metadata_score(path, project_root)
        metadata_rows.append(
            {
                "candidate_path": str(path),
                "file_type": "csv",
                "n_rows_if_readable": "preview" if info["readable"] else 0,
                "n_columns_if_readable": len(info.get("columns_found", [])),
                "id_column_found": "ecg_id" if "ecg_id" in info.get("columns_found", []) else "",
                "score": score,
                "reason": reason,
            }
        )
    metadata_rows = sorted(metadata_rows, key=lambda r: r["score"], reverse=True)
    selected_metadata = Path(metadata_rows[0]["candidate_path"]) if metadata_rows and metadata_rows[0]["score"] > 0 else None

    scp_candidates = _find_named_files(roots, "scp_statements.csv")
    scp_rows: list[dict[str, Any]] = []
    for path in scp_candidates:
        score, reason, info = _scp_score(path, selected_metadata, project_root)
        scp_rows.append(
            {
                "candidate_path": str(path),
                "file_type": "csv",
                "n_rows_if_readable": "preview" if info["readable"] else 0,
                "n_columns_if_readable": len(info.get("columns_found", [])),
                "id_column_found": "",
                "score": score,
                "reason": reason,
            }
        )
    scp_rows = sorted(scp_rows, key=lambda r: r["score"], reverse=True)
    selected_scp = Path(scp_rows[0]["candidate_path"]) if scp_rows and scp_rows[0]["score"] > 0 else None

    selected_waveform_base = None
    waveform_rows = pd.DataFrame()
    waveform_info = {"best_found": 0, "wfdb_installed": False, "wfdb_message": "metadata not found"}
    metadata_ids: set[str] | None = None
    if selected_metadata is not None:
        try:
            selected_waveform_base, waveform_rows, waveform_info = _check_waveform_bases(selected_metadata, project_root)
            meta_preview = pd.read_csv(selected_metadata, usecols=["ecg_id"])
            metadata_ids = set(meta_preview["ecg_id"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True))
        except Exception as exc:
            waveform_rows = pd.DataFrame(
                [
                    {
                        "candidate_path": "",
                        "file_type": "directory",
                        "n_rows_if_readable": 0,
                        "n_columns_if_readable": "",
                        "id_column_found": "",
                        "score": 0,
                        "reason": f"waveform check failed: {exc}",
                    }
                ]
            )

    feature_roots = _unique_existing(
        [
            project_root / "data" / "raw" / "ptbxl_plus",
            project_root / "data" / "raw",
            project_root,
            project_root.parent,
            project_root.parent.parent,
        ]
    )
    feature_files = _find_feature_files(feature_roots)
    plus_rows: list[dict[str, Any]] = []
    for path in feature_files:
        score, reason, info = _feature_score(path, project_root, metadata_ids=metadata_ids)
        exclude_reason = str(info.get("exclude_reason", ""))
        if score <= 0 and exclude_reason == "path does not contain PTB-XL+ feature keywords":
            continue
        if score <= 0 and not info.get("excluded"):
            continue
        plus_rows.append(
            {
                "candidate_path": str(path),
                "file_type": path.suffix.lower().lstrip("."),
                "n_rows_if_readable": info.get("n_rows", 0),
                "n_columns_if_readable": info.get("n_columns", 0),
                "id_column_found": info.get("id_column", ""),
                "score": score,
                "excluded": bool(info.get("excluded", False)),
                "exclude_reason": info.get("exclude_reason", ""),
                "reason": reason,
            }
        )
    plus_rows = sorted(plus_rows, key=lambda r: (r.get("excluded", False), -r["score"]))
    selected_plus = Path(plus_rows[0]["candidate_path"]) if plus_rows and not plus_rows[0].get("excluded") and plus_rows[0]["score"] >= 100 else None
    multiple_plus = len([r for r in plus_rows if not r.get("excluded") and r["score"] >= 100]) > 1

    candidate_df = pd.DataFrame(metadata_rows + scp_rows + waveform_rows.to_dict("records") + plus_rows)
    safe_to_csv(candidate_df, results_dir / "data_path_discovery_candidates.csv")

    config_updated, config_message = _update_config(
        config_path,
        project_root,
        selected_metadata,
        selected_scp,
        selected_waveform_base,
        selected_plus,
        multiple_plus,
    )

    if selected_metadata is None or selected_scp is None:
        blocking_issue = "PTB-XL metadata and/or scp_statements.csv were not found in the bounded search scope."
        user_action = """Please place PTB-XL files as follows:

```text
data/raw/ptbxl/ptbxl_database.csv
data/raw/ptbxl/scp_statements.csv
data/raw/ptbxl/records100/
data/raw/ptbxl/records500/
```

Please place PTB-XL+ structured features under:

```text
data/raw/ptbxl_plus/
```"""
        exit_code = 1
    elif selected_waveform_base is None:
        blocking_issue = "PTB-XL metadata was found, but waveform files could not be resolved from filename_lr/filename_hr."
        user_action = "Check that records100/ and records500/ are located next to ptbxl_database.csv or update records_base_dir manually."
        exit_code = 1
    else:
        blocking_issue = "None for PTB-XL path discovery. PTB-XL+ may still be absent if no structured feature candidate was selected."
        user_action = "Run Stage 0 and Stage 1 scripts to validate labels, folds, and processed outputs."
        exit_code = 0

    report = _report(
        roots,
        metadata_rows,
        scp_rows,
        waveform_rows,
        plus_rows,
        config_message,
        blocking_issue,
        user_action,
    )
    report += f"\n\nWaveform validation note: {waveform_info.get('wfdb_message', '')}\n"
    write_markdown(results_dir / "data_path_discovery_report.md", report)

    print("Data path discovery completed.")
    print(config_message)
    print(f"Report: {results_dir / 'data_path_discovery_report.md'}")
    print(f"Candidates: {results_dir / 'data_path_discovery_candidates.csv'}")
    print(f"Current blocking issue: {blocking_issue}")
    return exit_code


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover PTB-XL/PTB-XL+ paths and update config when safe.")
    parser.add_argument("--config", default="configs/data_ptbxl.yaml", help="Path to data_ptbxl.yaml")
    args = parser.parse_args()
    raise SystemExit(discover(args.config))


if __name__ == "__main__":
    main()
