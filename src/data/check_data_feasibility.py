from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Any

import pandas as pd

from src.data.label_mapping import (
    DEFAULT_SUPERCLASSES,
    build_ptbxl_superclass_labels,
    count_scp_parse_failures,
)
from src.utils.io import (
    ensure_dir,
    load_yaml,
    make_empty_csv,
    project_root_from_config,
    read_table_auto,
    resolve_path,
    safe_to_csv,
    write_markdown,
)

ID_CANDIDATES = ["ecg_id", "record_id", "id", "ECG_ID"]
FEATURE_SUFFIXES = [".csv", ".tsv", ".parquet", ".feather", ".pkl", ".pickle"]
EXCLUDED_FEATURE_FILENAMES = {
    "ptbxl_database.csv",
    "scp_statements.csv",
    "ptbxl_labels.csv",
    "ptbxl_train.csv",
    "ptbxl_val.csv",
    "ptbxl_test.csv",
}
PTBXL_PLUS_NOT_FOUND_MESSAGE = (
    "PTB-XL+ structured features not found. Current project can only run "
    "signal-only baseline until structured features are provided."
)


def _paths(config: dict[str, Any], root: Path) -> dict[str, Path | None]:
    ptbxl = config.get("ptbxl", {})
    plus = config.get("ptbxl_plus", {})
    output = config.get("output", {})
    return {
        "metadata_csv": resolve_path(ptbxl.get("metadata_csv"), root),
        "scp_statements_csv": resolve_path(ptbxl.get("scp_statements_csv"), root),
        "records_base_dir": resolve_path(ptbxl.get("records_base_dir"), root),
        "features_path": resolve_path(plus.get("features_path"), root),
        "features_csv": resolve_path(plus.get("features_csv"), root),
        "processed_dir": resolve_path(output.get("processed_dir", "data/processed"), root),
        "split_dir": resolve_path(output.get("split_dir", "data/splits"), root),
        "results_dir": resolve_path(output.get("results_dir", "results"), root),
        "tables_dir": resolve_path(output.get("tables_dir", "tables"), root),
    }


def _read_scp_statements(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, index_col=0)
    except Exception:
        return pd.read_csv(path)


def _empty_outputs(paths: dict[str, Path | None], classes: list[str] | None = None) -> None:
    classes = classes or DEFAULT_SUPERCLASSES
    tables_dir = paths["tables_dir"]
    assert tables_dir is not None
    safe_to_csv(
        pd.DataFrame(
            {
                "label": classes,
                "positive_count": [0] * len(classes),
                "metadata_missing": [True] * len(classes),
                "status": ["failed"] * len(classes),
            }
        ),
        tables_dir / "table_label_distribution.csv",
    )
    make_empty_csv(
        tables_dir / "table_structured_missingness.csv",
        ["feature", "missing_count", "missing_rate", "status"],
    )
    make_empty_csv(
        tables_dir / "table_split_distribution.csv",
        ["split", "n_samples", "NORM", "MI", "STTC", "CD", "HYP", "status"],
    )


def _find_feature_candidates(features_path: Path | None, explicit_file: Path | None) -> list[Path]:
    def is_allowed(path: Path) -> bool:
        return path.name.lower() not in EXCLUDED_FEATURE_FILENAMES

    candidates: list[Path] = []
    if explicit_file is not None:
        if explicit_file.exists() and explicit_file.is_file() and is_allowed(explicit_file):
            return [explicit_file]
        return []
    if features_path is None or not features_path.exists():
        return []
    if features_path.is_file() and features_path.suffix.lower() in FEATURE_SUFFIXES:
        return [features_path] if is_allowed(features_path) else []
    for suffix in FEATURE_SUFFIXES:
        candidates.extend(features_path.rglob(f"*{suffix}"))
    return sorted(set(path for path in candidates if is_allowed(path)))


def _normalise_id_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def _identify_id_column(df: pd.DataFrame) -> str | None:
    for col in ID_CANDIDATES:
        if col in df.columns:
            return col
    lower_map = {str(col).lower(): col for col in df.columns}
    for col in ID_CANDIDATES:
        if col.lower() in lower_map:
            return str(lower_map[col.lower()])
    return None


def _keyword_presence(columns: list[str]) -> dict[str, bool]:
    joined = " ".join(str(c).lower() for c in columns)
    return {
        "has_age": any(str(c).lower() == "age" or "age" in str(c).lower() for c in columns),
        "has_sex": any(str(c).lower() == "sex" or "gender" in str(c).lower() for c in columns),
        "has_interval_features": any(k in joined for k in ["interval", "pr", "qrs", "qt", "qtc", "pq"]),
        "has_axis_features": "axis" in joined or "axes" in joined,
        "has_amplitude_features": any(k in joined for k in ["amplitude", "amp", "volt"]),
    }


def _inspect_ptbxl_plus(
    candidates: list[Path], metadata_df: pd.DataFrame | None, tables_dir: Path
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "found": False,
        "selected_path": None,
        "candidate_paths": [str(p) for p in candidates],
        "id_column": None,
        "total_samples": 0,
        "aligned_samples": 0,
        "feature_count": 0,
        "non_numeric_columns": [],
        "read_errors": [],
        "keyword_presence": {
            "has_age": False,
            "has_sex": False,
            "has_interval_features": False,
            "has_axis_features": False,
            "has_amplitude_features": False,
        },
    }
    missingness_rows: list[dict[str, Any]] = []
    overview_rows: list[dict[str, Any]] = []

    metadata_ids = set()
    if metadata_df is not None and "ecg_id" in metadata_df.columns:
        metadata_ids = set(_normalise_id_series(metadata_df["ecg_id"]))

    best: tuple[int, Path, pd.DataFrame, str] | None = None
    for candidate in candidates:
        try:
            df = read_table_auto(candidate)
        except Exception as exc:  # Keep checking other candidates.
            result["read_errors"].append(f"{candidate}: {exc}")
            overview_rows.append(
                {
                    "path": str(candidate),
                    "readable": False,
                    "id_column": "",
                    "n_rows": 0,
                    "n_columns": 0,
                    "aligned_samples": 0,
                    "error": str(exc),
                }
            )
            continue
        id_col = _identify_id_column(df)
        aligned = 0
        if id_col and metadata_ids:
            aligned = int(_normalise_id_series(df[id_col]).isin(metadata_ids).sum())
        overview_rows.append(
            {
                "path": str(candidate),
                "readable": True,
                "id_column": id_col or "",
                "n_rows": len(df),
                "n_columns": len(df.columns),
                "aligned_samples": aligned,
                "error": "",
            }
        )
        if id_col:
            score = aligned if metadata_ids else len(df)
            if best is None or score > best[0]:
                best = (score, candidate, df, id_col)

    safe_to_csv(pd.DataFrame(overview_rows), tables_dir / "table_structured_features_overview.csv")

    if best is None:
        safe_to_csv(
            pd.DataFrame(columns=["feature", "missing_count", "missing_rate", "status"]),
            tables_dir / "table_structured_missingness.csv",
        )
        if candidates:
            result["alignment_reason"] = "PTB-XL+ candidate files were found, but none had a supported ID column."
        else:
            result["alignment_reason"] = PTBXL_PLUS_NOT_FOUND_MESSAGE
        return result

    _, selected_path, df, id_col = best
    result["found"] = True
    result["selected_path"] = str(selected_path)
    result["id_column"] = id_col
    result["total_samples"] = int(len(df))
    if metadata_ids:
        aligned_mask = _normalise_id_series(df[id_col]).isin(metadata_ids)
        result["aligned_samples"] = int(aligned_mask.sum())
    else:
        aligned_mask = pd.Series([True] * len(df), index=df.index)
        result["aligned_samples"] = int(len(df))

    non_id_cols = [c for c in df.columns if c != id_col]
    result["feature_count"] = int(len(non_id_cols))
    result["non_numeric_columns"] = [
        str(c) for c in non_id_cols if not pd.api.types.is_numeric_dtype(df[c])
    ]
    result["keyword_presence"] = _keyword_presence([str(c) for c in df.columns])

    for col in non_id_cols:
        missing_count = int(df[col].isna().sum())
        missing_rate = float(df[col].isna().mean()) if len(df) else 0.0
        missingness_rows.append(
            {"feature": col, "missing_count": missing_count, "missing_rate": missing_rate, "status": "success"}
        )
    missingness_df = pd.DataFrame(missingness_rows)
    if not missingness_df.empty:
        missingness_df = missingness_df.sort_values("missing_rate", ascending=False)
    safe_to_csv(missingness_df, tables_dir / "table_structured_missingness.csv")
    return result


def _check_waveforms(metadata_df: pd.DataFrame | None, paths: dict[str, Path | None], config: dict[str, Any]) -> dict[str, Any]:
    ptbxl = config.get("ptbxl", {})
    waveform_col = ptbxl.get("waveform_column_100hz", "filename_lr")
    records_base_dir = paths["records_base_dir"]
    info: dict[str, Any] = {
        "column": waveform_col,
        "checked": 0,
        "existing_records": 0,
        "missing_records": 0,
        "missing_examples": [],
        "wfdb_installed": importlib.util.find_spec("wfdb") is not None,
        "wfdb_probe_ok": None,
        "wfdb_probe_message": "",
        "status": "failed",
    }
    if metadata_df is None:
        info["wfdb_probe_message"] = "Metadata not available; waveform paths were not checked."
        return info
    if records_base_dir is None or not records_base_dir.exists():
        info["wfdb_probe_message"] = f"Waveform base directory not found: {records_base_dir}"
        return info
    if waveform_col not in metadata_df.columns:
        info["wfdb_probe_message"] = f"Waveform column not found in metadata: {waveform_col}"
        return info

    sample = metadata_df[waveform_col].dropna().head(20)
    for rel_record in sample:
        record_base = records_base_dir / str(rel_record)
        hea_path = record_base.with_suffix(".hea")
        dat_path = record_base.with_suffix(".dat")
        info["checked"] += 1
        if hea_path.exists() and dat_path.exists():
            info["existing_records"] += 1
        else:
            info["missing_records"] += 1
            if len(info["missing_examples"]) < 5:
                info["missing_examples"].append(str(record_base))

    if info["wfdb_installed"] and info["existing_records"] > 0:
        try:
            import wfdb  # type: ignore

            first_existing = None
            for rel_record in sample:
                record_base = records_base_dir / str(rel_record)
                if record_base.with_suffix(".hea").exists() and record_base.with_suffix(".dat").exists():
                    first_existing = record_base
                    break
            if first_existing is not None:
                header = wfdb.rdheader(str(first_existing))
                info["wfdb_probe_ok"] = True
                info["wfdb_probe_message"] = (
                    f"wfdb header ok: fs={getattr(header, 'fs', '')}, "
                    f"sig_len={getattr(header, 'sig_len', '')}, n_sig={getattr(header, 'n_sig', '')}"
                )
        except Exception as exc:
            info["wfdb_probe_ok"] = False
            info["wfdb_probe_message"] = f"wfdb probe failed: {exc}"
    elif not info["wfdb_installed"]:
        info["wfdb_probe_message"] = "wfdb is not installed. File existence check was performed, but waveform loading was not validated."
    if info["checked"] > 0 and info["existing_records"] > 0 and info["missing_records"] == 0:
        info["status"] = "success"
    elif info["checked"] > 0 and info["existing_records"] > 0:
        info["status"] = "partial"
    return info


def _split_distribution(metadata_df: pd.DataFrame, labels_df: pd.DataFrame, classes: list[str]) -> pd.DataFrame:
    merged = metadata_df[["ecg_id", "strat_fold"]].merge(labels_df, on="ecg_id", how="left")
    split_defs = {
        "train": merged["strat_fold"].isin(list(range(1, 9))),
        "val": merged["strat_fold"].eq(9),
        "test": merged["strat_fold"].eq(10),
    }
    rows = []
    for split, mask in split_defs.items():
        subset = merged[mask]
        row = {"split": split, "n_samples": int(len(subset)), "status": "success" if len(subset) > 0 else "failed"}
        for label in classes:
            row[label] = int(subset[label].fillna(0).sum()) if label in subset.columns else 0
        rows.append(row)
    fold_counts = merged["strat_fold"].value_counts(dropna=False).sort_index()
    for fold, count in fold_counts.items():
        rows.append({"split": f"fold_{fold}", "n_samples": int(count), **{c: "" for c in classes}, "status": "success"})
    return pd.DataFrame(rows)


def _summary_row(group: str, name: str, status: str, detail: str) -> dict[str, str]:
    return {"check_group": group, "check_name": name, "status": status, "detail": detail}


def _build_report(
    metadata_found: bool,
    scp_found: bool,
    metadata_info: dict[str, Any],
    waveform_info: dict[str, Any],
    label_distribution: pd.DataFrame,
    plus_info: dict[str, Any],
    split_distribution: pd.DataFrame,
    conclusion: str,
    recommendation: str,
) -> str:
    label_md = label_distribution.to_markdown(index=False) if not label_distribution.empty else "No labels available."
    split_md = split_distribution.to_markdown(index=False) if not split_distribution.empty else "No split information available."
    candidates = plus_info.get("candidate_paths", [])
    candidate_text = "\n".join(f"- {p}" for p in candidates) if candidates else "No candidate files found."
    missing_top = "See `tables/table_structured_missingness.csv` for missingness details."
    non_numeric = plus_info.get("non_numeric_columns", [])[:50]
    keyword_presence = plus_info.get("keyword_presence", {})

    return f"""# Data Feasibility Report

## 1. PTB-XL Metadata Check

- ptbxl_database.csv found: {'yes' if metadata_found else 'no'}
- scp_statements.csv found: {'yes' if scp_found else 'no'}
- metadata rows: {metadata_info.get('n_rows', 0)}
- metadata columns: {metadata_info.get('n_columns', 0)}
- missing required columns: {', '.join(metadata_info.get('missing_columns', [])) or 'none'}
- SCP parse failures: {metadata_info.get('scp_parse_failures', 0)}

## 2. Waveform File Check

- waveform column: {waveform_info.get('column')}
- first records checked: {waveform_info.get('checked', 0)}
- waveform files found: {waveform_info.get('existing_records', 0)}
- waveform files missing: {waveform_info.get('missing_records', 0)}
- waveform status: {waveform_info.get('status', 'failed')}
- missing examples: {', '.join(waveform_info.get('missing_examples', [])) or 'none'}
- wfdb installed: {'yes' if waveform_info.get('wfdb_installed') else 'no'}
- wfdb probe: {waveform_info.get('wfdb_probe_message', '')}

## 3. Diagnostic Superclass Label Distribution

{label_md}

## 4. PTB-XL+ Structured Feature Check

- PTB-XL+ found: {'yes' if plus_info.get('found') else 'no'}
- selected feature file: {plus_info.get('selected_path') or 'none'}
- candidate files:
{candidate_text}
- total structured rows: {plus_info.get('total_samples', 0)}
- structured feature columns: {plus_info.get('feature_count', 0)}
- non-numeric columns: {', '.join(map(str, non_numeric)) or 'none'}
- has age: {'yes' if keyword_presence.get('has_age') else 'no'}
- has sex: {'yes' if keyword_presence.get('has_sex') else 'no'}
- has interval features: {'yes' if keyword_presence.get('has_interval_features') else 'no'}
- has axis features: {'yes' if keyword_presence.get('has_axis_features') else 'no'}
- has amplitude features: {'yes' if keyword_presence.get('has_amplitude_features') else 'no'}

{'' if plus_info.get('found') else PTBXL_PLUS_NOT_FOUND_MESSAGE}

{missing_top}

## 5. PTB-XL and PTB-XL+ Alignment

- ID column: {plus_info.get('id_column') or 'none'}
- aligned multimodal samples: {plus_info.get('aligned_samples', 0)}
- alignment reason: {plus_info.get('alignment_reason', 'alignment succeeded' if plus_info.get('aligned_samples', 0) > 0 else 'no aligned samples found')}

## 6. Official Fold Split Check

{split_md}

## 7. Feasibility Conclusion

{conclusion}

## 8. Recommended Next Step

{recommendation}
"""


def run(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    paths = _paths(config, root)

    for key in ["processed_dir", "split_dir", "results_dir", "tables_dir"]:
        assert paths[key] is not None
        ensure_dir(paths[key])

    classes = config.get("task", {}).get("diagnostic_superclasses", DEFAULT_SUPERCLASSES)
    _empty_outputs(paths, classes)
    required_columns = ["ecg_id", "scp_codes", "strat_fold", "filename_lr", "filename_hr"]
    summary_rows: list[dict[str, str]] = []

    metadata_path = paths["metadata_csv"]
    scp_path = paths["scp_statements_csv"]
    metadata_found = bool(metadata_path and metadata_path.exists())
    scp_found = bool(scp_path and scp_path.exists())
    summary_rows.append(
        _summary_row(
            "metadata",
            "ptbxl_database_csv",
            "pass" if metadata_found else "failed",
            f"found at {metadata_path}" if metadata_found else f"missing; place ptbxl_database.csv at {metadata_path}",
        )
    )
    summary_rows.append(
        _summary_row(
            "metadata",
            "scp_statements_csv",
            "pass" if scp_found else "failed",
            f"found at {scp_path}" if scp_found else f"missing; place scp_statements.csv at {scp_path}",
        )
    )

    metadata_df = None
    scp_df = None
    labels_df = pd.DataFrame(columns=["ecg_id"] + classes)
    label_distribution = pd.DataFrame(
        {
            "label": classes,
            "positive_count": [0] * len(classes),
            "metadata_missing": [True] * len(classes),
            "status": ["failed"] * len(classes),
        }
    )
    split_distribution = pd.DataFrame(columns=["split", "n_samples"] + classes + ["status"])
    metadata_info = {"n_rows": 0, "n_columns": 0, "missing_columns": required_columns, "scp_parse_failures": 0}

    if metadata_found and scp_found:
        metadata_df = pd.read_csv(metadata_path)
        scp_df = _read_scp_statements(scp_path)
        missing_columns = [col for col in required_columns if col not in metadata_df.columns]
        metadata_info = {
            "n_rows": int(len(metadata_df)),
            "n_columns": int(len(metadata_df.columns)),
            "missing_columns": missing_columns,
            "scp_parse_failures": count_scp_parse_failures(metadata_df),
        }
        summary_rows.append(
            _summary_row(
                "metadata",
                "required_columns",
                "success" if not missing_columns else "failed",
                "all required columns found" if not missing_columns else f"missing columns: {missing_columns}",
            )
        )
        if not missing_columns:
            labels_df = build_ptbxl_superclass_labels(metadata_df, scp_df, classes=classes)
            label_distribution = pd.DataFrame(
                {
                    "label": classes,
                    "positive_count": [int(labels_df[c].sum()) for c in classes],
                    "metadata_missing": [False] * len(classes),
                    "status": ["success"] * len(classes),
                }
            )
            safe_to_csv(label_distribution, paths["tables_dir"] / "table_label_distribution.csv")
            split_distribution = _split_distribution(metadata_df, labels_df, classes)
            safe_to_csv(split_distribution, paths["tables_dir"] / "table_split_distribution.csv")
    else:
        summary_rows.append(
            _summary_row("metadata", "required_columns", "failed", "metadata files missing; columns not checked")
        )

    waveform_info = _check_waveforms(metadata_df, paths, config)
    waveform_ok = waveform_info.get("existing_records", 0) > 0 and waveform_info.get("missing_records", 0) == 0
    if metadata_df is not None and waveform_info.get("checked", 0) > 0:
        wf_status = waveform_info.get("status", "failed")
    else:
        wf_status = "failed"
    summary_rows.append(
        _summary_row(
            "waveform",
            "first_20_records",
            wf_status,
            f"checked={waveform_info.get('checked', 0)}, found={waveform_info.get('existing_records', 0)}, missing={waveform_info.get('missing_records', 0)}",
        )
    )

    candidates = _find_feature_candidates(paths["features_path"], paths["features_csv"])
    plus_info = _inspect_ptbxl_plus(candidates, metadata_df, paths["tables_dir"])
    summary_rows.append(
        _summary_row(
            "ptbxl_plus",
            "structured_features",
            "success" if plus_info.get("found") and plus_info.get("aligned_samples", 0) > 0 else ("partial" if plus_info.get("found") else "partial"),
            f"selected={plus_info.get('selected_path')}, aligned={plus_info.get('aligned_samples', 0)}"
            if plus_info.get("found")
            else plus_info.get("alignment_reason", PTBXL_PLUS_NOT_FOUND_MESSAGE),
        )
    )

    metadata_usable = metadata_found and scp_found and metadata_df is not None and not metadata_info.get("missing_columns")
    if not metadata_usable or not waveform_ok:
        conclusion = "Conclusion: Not feasible until PTB-XL raw data are correctly placed."
        recommendation = "Fix PTB-XL metadata and waveform paths first, then rerun Stage 0."
        stage0_status = "failed"
    elif plus_info.get("found") and plus_info.get("aligned_samples", 0) > 0:
        conclusion = "Conclusion: Feasible for multimodal ECG decision-support modeling."
        recommendation = "Hand over to Codex for multimodal baseline after Stage 1 data preparation."
        stage0_status = "success"
    else:
        conclusion = "Conclusion: Feasible for signal-only ECG modeling, but not yet feasible for multimodal modeling."
        recommendation = "Recommended next step: provide PTB-XL+ structured feature files."
        stage0_status = "partial"

    summary_rows.append(_summary_row("feasibility", "conclusion", stage0_status, conclusion))
    safe_to_csv(pd.DataFrame(summary_rows), paths["results_dir"] / "data_feasibility_summary.csv")

    report = _build_report(
        metadata_found,
        scp_found,
        metadata_info,
        waveform_info,
        label_distribution,
        plus_info,
        split_distribution,
        conclusion,
        recommendation,
    )
    write_markdown(paths["results_dir"] / "data_feasibility_report.md", report)

    print("Stage 0 data feasibility check completed.")
    print(conclusion)
    print(f"Report: {paths['results_dir'] / 'data_feasibility_report.md'}")

    return 1 if (not metadata_usable or not waveform_ok) else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Check PTB-XL/PTB-XL+ data feasibility without training models.")
    parser.add_argument("--config", required=True, help="Path to configs/data_ptbxl.yaml")
    args = parser.parse_args()
    raise SystemExit(run(args.config))


if __name__ == "__main__":
    main()
