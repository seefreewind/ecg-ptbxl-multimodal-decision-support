from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data.validate_ptbxl_plus import identify_id_column
from src.utils.io import ensure_dir, load_yaml, project_root_from_config, read_table_auto, resolve_path, safe_to_csv, write_markdown

LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
EXACT_EXCLUDE_COLUMNS = {
    "ecg_id",
    "patient_id",
    "recording_date",
    "scp_codes",
    "diagnostic_class",
    "diagnostic_subclass",
    "diagnostic",
    "statement",
    "snomed",
    "label",
    "target",
    "fold",
    "strat_fold",
    "filename_lr",
    "filename_hr",
}
LEAKAGE_COLUMN_KEYWORDS = ["diagnostic", "statement", "snomed", "scp", "label", "target", "class", "subclass"]
MISSING_RATE_THRESHOLD = 0.40


def _selected_feature_file(results_dir: Path) -> Path | None:
    candidates_path = results_dir / "ptbxl_plus_candidates.csv"
    if not candidates_path.exists():
        return None
    candidates = pd.read_csv(candidates_path)
    if candidates.empty or "selected" not in candidates.columns:
        return None
    selected = candidates[candidates["selected"].astype(str).str.lower().eq("true")]
    if selected.empty:
        return None
    path_col = "candidate_path" if "candidate_path" in selected.columns else "path"
    path = Path(str(selected.iloc[0][path_col]))
    return path if path.exists() else None


def _default_feature_file(root: Path) -> Path | None:
    base = root / "data" / "raw" / "ptbxl_plus" / "features"
    for name in ["ecgdeli_features.csv", "12sl_features.csv", "unig_features.csv"]:
        path = base / name
        if path.exists():
            return path
    return None


def standardise_ecg_id(df: pd.DataFrame, id_col: str) -> pd.Series:
    ids = pd.to_numeric(df[id_col], errors="coerce")
    if ids.isna().any():
        bad = int(ids.isna().sum())
        raise ValueError(f"ID column {id_col} contains {bad} values that cannot be converted to int.")
    return ids.astype("int64")


def _split_from_fold(fold: int) -> str:
    if 1 <= int(fold) <= 8:
        return "train"
    if int(fold) == 9:
        return "val"
    if int(fold) == 10:
        return "test"
    return "unknown"


def _blocking_report(message: str) -> str:
    return f"""# PTB-XL+ Alignment Report

## Status

failed

## Blocking Issue

{message}

## Recommended Next Action

Run `bash scripts/01b_validate_ptbxl_plus.sh` after placing valid PTB-XL+ structured feature files under `data/raw/ptbxl_plus/`.
"""


def classify_feature_columns(df: pd.DataFrame, id_col: str, missing_rate_threshold: float = MISSING_RATE_THRESHOLD) -> tuple[list[str], pd.DataFrame, pd.DataFrame]:
    kept: list[str] = []
    missingness_rows = []
    excluded_rows = []
    for col in df.columns:
        col_lower = str(col).lower()
        if col == id_col or col_lower == "ecg_id":
            excluded_rows.append({"column": col, "dtype": str(df[col].dtype), "drop_reason": "identifier"})
            continue
        if col_lower in EXACT_EXCLUDE_COLUMNS:
            excluded_rows.append({"column": col, "dtype": str(df[col].dtype), "drop_reason": "reserved or metadata column"})
            continue
        if any(keyword in col_lower for keyword in LEAKAGE_COLUMN_KEYWORDS):
            excluded_rows.append({"column": col, "dtype": str(df[col].dtype), "drop_reason": "potential diagnostic label leakage keyword"})
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            excluded_rows.append({"column": col, "dtype": str(df[col].dtype), "drop_reason": "non-numeric column"})
            continue
        missing_rate = float(df[col].isna().mean()) if len(df) else 0.0
        keep = missing_rate <= missing_rate_threshold
        missingness_rows.append(
            {
                "feature": col,
                "missing_count": int(df[col].isna().sum()),
                "missing_rate": missing_rate,
                "dtype": str(df[col].dtype),
                "kept_for_modeling": keep,
                "drop_reason": "" if keep else "missing_rate > 0.40",
            }
        )
        if keep:
            kept.append(str(col))
        else:
            excluded_rows.append({"column": col, "dtype": str(df[col].dtype), "drop_reason": "missing_rate > 0.40"})
    return kept, pd.DataFrame(missingness_rows), pd.DataFrame(excluded_rows)


def align(config_path: str | Path = "configs/data_ptbxl.yaml") -> int:
    config_path = Path(config_path)
    root = project_root_from_config(config_path)
    config = load_yaml(config_path)
    output = config.get("output", {})
    results_dir = ensure_dir(resolve_path(output.get("results_dir", "results"), root))
    processed_dir = ensure_dir(resolve_path(output.get("processed_dir", "data/processed"), root))
    tables_dir = ensure_dir(resolve_path(output.get("tables_dir", "tables"), root))

    labels_path = processed_dir / "ptbxl_labels.csv"
    selected_file = _selected_feature_file(results_dir) or _default_feature_file(root)
    if selected_file is None:
        message = "No validated PTB-XL+ feature file is selected. Multimodal alignment is blocked."
        write_markdown(results_dir / "ptbxl_plus_alignment_report.md", _blocking_report(message))
        print(message)
        return 1
    if "/labels/" in selected_file.as_posix().lower() or not selected_file.as_posix().lower().endswith(("ecgdeli_features.csv", "12sl_features.csv", "unig_features.csv")):
        message = f"Selected file is not a leakage-safe PTB-XL+ features table: {selected_file}"
        write_markdown(results_dir / "ptbxl_plus_alignment_report.md", _blocking_report(message))
        print(message)
        return 1
    if not labels_path.exists():
        message = "PTB-XL labels are missing. Run Stage 1 PTB-XL preparation before PTB-XL+ alignment."
        write_markdown(results_dir / "ptbxl_plus_alignment_report.md", _blocking_report(message))
        print(message)
        return 1

    ptbxl = pd.read_csv(labels_path)
    plus = read_table_auto(selected_file)
    id_col = identify_id_column([str(col) for col in plus.columns])
    if not id_col:
        message = f"Selected PTB-XL+ file has no supported ID column: {selected_file}"
        write_markdown(results_dir / "ptbxl_plus_alignment_report.md", _blocking_report(message))
        print(message)
        return 1

    plus = plus.copy()
    ptbxl = ptbxl.copy()
    try:
        plus["ecg_id"] = standardise_ecg_id(plus, id_col)
        ptbxl["ecg_id"] = standardise_ecg_id(ptbxl, "ecg_id")
    except ValueError as exc:
        write_markdown(results_dir / "ptbxl_plus_alignment_report.md", _blocking_report(str(exc)))
        print(str(exc))
        return 1

    raw_feature_columns = [col for col in plus.columns if col not in {id_col, "ecg_id"}]
    kept_features, missingness_df, excluded_columns_df = classify_feature_columns(plus, id_col=id_col)
    structured = plus[["ecg_id"] + kept_features].drop_duplicates("ecg_id")
    aligned = ptbxl.merge(structured, on="ecg_id", how="left", indicator=True)
    aligned_rows = int(aligned["_merge"].eq("both").sum())
    alignment_rate_vs_ptbxl = float(aligned_rows / len(ptbxl)) if len(ptbxl) else 0.0
    alignment_rate_vs_plus = float(aligned_rows / len(plus)) if len(plus) else 0.0

    safe_to_csv(structured, processed_dir / "ptbxl_structured_features.csv")
    (processed_dir / "structured_feature_names.txt").write_text("\n".join(kept_features) + ("\n" if kept_features else ""), encoding="utf-8")
    index = ptbxl[["ecg_id", "filename_lr", "filename_hr", "strat_fold"] + LABELS].copy()
    index["split"] = index["strat_fold"].apply(_split_from_fold)
    index["has_waveform"] = True
    index["has_structured"] = index["ecg_id"].isin(set(structured["ecg_id"]))
    index = index[["ecg_id", "filename_lr", "filename_hr", "strat_fold", "split", "has_waveform", "has_structured"] + LABELS]
    safe_to_csv(index, processed_dir / "ptbxl_multimodal_index.csv")

    safe_to_csv(missingness_df.sort_values("missing_rate", ascending=False), tables_dir / "table_ptbxl_plus_missingness.csv")
    safe_to_csv(excluded_columns_df, tables_dir / "table_ptbxl_plus_excluded_columns.csv")
    success = aligned_rows > 10000 and len(kept_features) > 20
    alignment_table = pd.DataFrame(
        [
            {
                "source_feature_file": str(selected_file),
                "ptbxl_rows": len(ptbxl),
                "ptbxl_plus_rows": len(plus),
                "aligned_rows": aligned_rows,
                "alignment_rate_vs_ptbxl": alignment_rate_vs_ptbxl,
                "alignment_rate_vs_ptbxl_plus": alignment_rate_vs_plus,
                "raw_feature_columns": len(raw_feature_columns),
                "numeric_feature_columns": int(sum(pd.api.types.is_numeric_dtype(plus[col]) for col in raw_feature_columns)),
                "kept_feature_columns": len(kept_features),
                "dropped_feature_columns": len(excluded_columns_df),
                "missing_rate_threshold": MISSING_RATE_THRESHOLD,
                "status": "ready" if success else "blocked",
            }
        ]
    )
    safe_to_csv(alignment_table, tables_dir / "table_ptbxl_plus_alignment.csv")
    top_missing = missingness_df.sort_values("missing_rate", ascending=False).head(30).to_markdown(index=False) if not missingness_df.empty else "No numeric structured features."
    report = f"""# PTB-XL+ Alignment Report

## Status

{"ready" if success else "blocked"}

## Selected Feature File

{selected_file}

## Alignment Summary

- PTB-XL rows: {len(ptbxl)}
- PTB-XL+ rows: {len(plus)}
- aligned rows: {aligned_rows}
- alignment rate vs PTB-XL: {alignment_rate_vs_ptbxl:.6f}
- alignment rate vs PTB-XL+: {alignment_rate_vs_plus:.6f}
- raw feature columns: {len(raw_feature_columns)}
- kept feature columns: {len(kept_features)}
- dropped feature columns: {len(excluded_columns_df)}

## Missingness Top 30

{top_missing}

## Blocking Issue

{"" if success else "PTB-XL+ alignment did not meet success criteria: aligned rows > 10000 and kept feature columns > 20."}
"""
    write_markdown(results_dir / "ptbxl_plus_alignment_report.md", report)
    print("PTB-XL+ alignment completed.")
    print(f"Aligned rows: {aligned_rows}")
    print(f"Kept feature columns: {len(kept_features)}")
    return 0 if success else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Align validated leakage-safe PTB-XL+ structured features to PTB-XL labels.")
    parser.add_argument("--config", default="configs/data_ptbxl.yaml")
    args = parser.parse_args()
    raise SystemExit(align(args.config))


if __name__ == "__main__":
    main()
