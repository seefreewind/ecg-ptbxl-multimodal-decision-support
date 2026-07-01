from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import (
    ensure_dir,
    load_yaml,
    make_empty_csv,
    project_root_from_config,
    read_table_auto,
    resolve_path,
    safe_to_csv,
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
NOT_FOUND_MESSAGE = (
    "PTB-XL+ structured features not found. Current project can only run "
    "signal-only baseline until structured features are provided."
)


def _paths(config: dict[str, Any], root: Path) -> dict[str, Path | None]:
    ptbxl = config.get("ptbxl", {})
    plus = config.get("ptbxl_plus", {})
    output = config.get("output", {})
    return {
        "metadata_csv": resolve_path(ptbxl.get("metadata_csv"), root),
        "features_path": resolve_path(plus.get("features_path"), root),
        "features_csv": resolve_path(plus.get("features_csv"), root),
        "processed_dir": resolve_path(output.get("processed_dir", "data/processed"), root),
        "tables_dir": resolve_path(output.get("tables_dir", "tables"), root),
    }


def _find_candidates(features_path: Path | None, explicit_file: Path | None) -> list[Path]:
    def is_allowed(path: Path) -> bool:
        return path.name.lower() not in EXCLUDED_FEATURE_FILENAMES

    if explicit_file is not None:
        return [explicit_file] if explicit_file.exists() and explicit_file.is_file() and is_allowed(explicit_file) else []
    if features_path is None or not features_path.exists():
        return []
    if features_path.is_file() and features_path.suffix.lower() in FEATURE_SUFFIXES:
        return [features_path] if is_allowed(features_path) else []
    candidates: list[Path] = []
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


def _load_ptbxl_ids(paths: dict[str, Path | None]) -> pd.Series | None:
    processed_dir = paths["processed_dir"]
    labels_path = processed_dir / "ptbxl_labels.csv"
    if labels_path.exists():
        labels_df = pd.read_csv(labels_path, usecols=["ecg_id"])
        if labels_df.empty:
            return None
        return labels_df["ecg_id"]
    metadata_path = paths["metadata_csv"]
    if metadata_path is None or not metadata_path.exists():
        return None
    metadata_df = pd.read_csv(metadata_path, usecols=["ecg_id"])
    if metadata_df.empty:
        return None
    return metadata_df["ecg_id"]


def _write_not_found_outputs(tables_dir: Path) -> None:
    safe_to_csv(
        pd.DataFrame(
            [
                {
                    "found": False,
                    "selected_path": "",
                    "n_rows": 0,
                    "n_numeric_features": 0,
                    "aligned_samples": 0,
                    "status": "partial",
                    "message": NOT_FOUND_MESSAGE,
                }
            ]
        ),
        tables_dir / "table_structured_features_overview.csv",
    )
    make_empty_csv(tables_dir / "table_structured_missingness.csv", ["feature", "missing_count", "missing_rate", "status"])


def _write_status(tables_dir: Path, status: str, detail: str) -> None:
    safe_to_csv(
        pd.DataFrame([{"stage": "prepare_ptbxl_plus", "status": status, "detail": detail}]),
        tables_dir / "table_prepare_ptbxl_plus_status.csv",
    )


def prepare_plus(config_path: str | Path) -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    paths = _paths(config, root)
    processed_dir = ensure_dir(paths["processed_dir"])
    tables_dir = ensure_dir(paths["tables_dir"])

    ptbxl_id_series = _load_ptbxl_ids(paths)
    if ptbxl_id_series is None:
        detail = "PTB-XL labels or metadata were not available, so PTB-XL+ alignment was skipped. Run prepare_ptbxl.py after fixing metadata paths."
        _write_status(tables_dir, "partial", detail)
        _write_not_found_outputs(tables_dir)
        print(f"WARNING: {detail}")
        return 0

    ptbxl_ids = set(_normalise_id_series(ptbxl_id_series))
    candidates = _find_candidates(paths["features_path"], paths["features_csv"])
    if not candidates:
        _write_not_found_outputs(tables_dir)
        _write_status(tables_dir, "partial", NOT_FOUND_MESSAGE)
        print(f"WARNING: {NOT_FOUND_MESSAGE}")
        return 0

    overview_rows: list[dict[str, Any]] = []
    best: tuple[int, Path, pd.DataFrame, str] | None = None
    for candidate in candidates:
        try:
            df = read_table_auto(candidate)
            id_col = _identify_id_column(df)
            aligned = 0
            if id_col:
                aligned = int(_normalise_id_series(df[id_col]).isin(ptbxl_ids).sum())
            overview_rows.append(
                {
                    "found": True,
                    "path": str(candidate),
                    "readable": True,
                    "id_column": id_col or "",
                    "n_rows": len(df),
                    "n_columns": len(df.columns),
                    "aligned_samples": aligned,
                    "error": "",
                }
            )
            if id_col and (best is None or aligned > best[0]):
                best = (aligned, candidate, df, id_col)
        except Exception as exc:
            overview_rows.append(
                {
                    "found": True,
                    "path": str(candidate),
                    "readable": False,
                    "id_column": "",
                    "n_rows": 0,
                    "n_columns": 0,
                    "aligned_samples": 0,
                    "error": str(exc),
                }
            )

    if best is None or best[0] == 0:
        safe_to_csv(pd.DataFrame(overview_rows), tables_dir / "table_structured_features_overview.csv")
        make_empty_csv(tables_dir / "table_structured_missingness.csv", ["feature", "missing_count", "missing_rate", "status"])
        if best is None:
            detail = "PTB-XL+ files were found, but none had a supported ID column: ecg_id, record_id, id, or ECG_ID."
        else:
            detail = "PTB-XL+ files were found and had ID columns, but zero rows matched PTB-XL ecg_id values."
        _write_status(tables_dir, "partial", detail)
        print(f"WARNING: {detail}")
        return 0

    aligned_count, selected_path, df, id_col = best
    df = df.copy()
    df["ecg_id"] = _normalise_id_series(df[id_col])
    aligned_df = df[df["ecg_id"].isin(ptbxl_ids)].copy()

    feature_candidates = [c for c in aligned_df.columns if c not in {id_col, "ecg_id"}]
    numeric_features = [c for c in feature_candidates if pd.api.types.is_numeric_dtype(aligned_df[c])]
    non_numeric_features = [c for c in feature_candidates if c not in numeric_features]
    output_df = aligned_df[["ecg_id"] + numeric_features]
    safe_to_csv(output_df, processed_dir / "ptbxl_structured_features.csv")

    (processed_dir / "structured_feature_names.txt").write_text(
        "\n".join(map(str, numeric_features)) + ("\n" if numeric_features else ""),
        encoding="utf-8",
    )

    missingness_rows = []
    for col in numeric_features:
        missingness_rows.append(
            {
                "feature": col,
                "missing_count": int(output_df[col].isna().sum()),
                "missing_rate": float(output_df[col].isna().mean()) if len(output_df) else 0.0,
                "status": "success",
            }
        )
    missingness_df = pd.DataFrame(missingness_rows)
    if not missingness_df.empty:
        missingness_df = missingness_df.sort_values("missing_rate", ascending=False)
    safe_to_csv(missingness_df, tables_dir / "table_structured_missingness.csv")

    overview_rows.append(
        {
            "found": True,
            "path": str(selected_path),
            "readable": True,
            "id_column": id_col,
            "n_rows": len(df),
            "n_columns": len(df.columns),
            "aligned_samples": aligned_count,
            "n_numeric_features": len(numeric_features),
            "non_numeric_columns": ";".join(map(str, non_numeric_features)),
            "selected": True,
            "status": "success",
            "error": "",
        }
    )
    safe_to_csv(pd.DataFrame(overview_rows), tables_dir / "table_structured_features_overview.csv")
    _write_status(tables_dir, "success", f"generated structured features from {selected_path}; aligned_samples={aligned_count}; numeric_features={len(numeric_features)}")

    print("Stage 1 PTB-XL+ structured feature preparation completed.")
    print("Status: success")
    print(f"Selected PTB-XL+ file: {selected_path}")
    print(f"Aligned multimodal samples: {aligned_count}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare PTB-XL+ structured features without training models.")
    parser.add_argument("--config", required=True, help="Path to configs/data_ptbxl.yaml")
    args = parser.parse_args()
    raise SystemExit(prepare_plus(args.config))


if __name__ == "__main__":
    main()
