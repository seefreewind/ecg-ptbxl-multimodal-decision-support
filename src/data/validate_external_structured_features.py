from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


COLUMNS = [
    "dataset",
    "feature_table",
    "exists",
    "n_rows",
    "n_columns",
    "required_feature_count",
    "matched_required_features",
    "missing_required_features",
    "extra_feature_columns",
    "has_record_id",
    "has_source_dataset",
    "nonempty",
    "schema_exact_match",
    "can_run_multimodal_external_validation",
    "blocking_issue",
]


def _required_features() -> list[str]:
    return [line.strip() for line in Path("data/processed/structured_feature_names.txt").read_text().splitlines() if line.strip()]


def _candidate_tables() -> dict[str, Path]:
    cfg = load_yaml("configs/external_structured_features.yaml")
    configured = cfg.get("external", {}).get("candidate_feature_tables", {})
    return {
        "cpsc2018": Path(configured.get("cpsc2018", "data/processed/external/cpsc2018_structured_features.csv")),
        "chapman": Path(configured.get("chapman", "data/processed/external/chapman_structured_features.csv")),
    }


def validate() -> pd.DataFrame:
    required = _required_features()
    required_set = set(required)
    rows: list[dict[str, Any]] = []
    for dataset, path in _candidate_tables().items():
        row: dict[str, Any] = {
            "dataset": dataset,
            "feature_table": str(path),
            "exists": path.exists(),
            "n_rows": 0,
            "n_columns": 0,
            "required_feature_count": len(required),
            "matched_required_features": 0,
            "missing_required_features": len(required),
            "extra_feature_columns": 0,
            "has_record_id": False,
            "has_source_dataset": False,
            "nonempty": False,
            "schema_exact_match": False,
            "can_run_multimodal_external_validation": False,
            "blocking_issue": "external_structured_feature_table_missing",
        }
        if path.exists():
            try:
                df = pd.read_csv(path)
                cols = set(map(str, df.columns))
                feature_cols = cols - {"record_id", "source_dataset"}
                missing = required_set - cols
                extra = feature_cols - required_set
                row.update(
                    {
                        "n_rows": len(df),
                        "n_columns": len(df.columns),
                        "matched_required_features": len(required_set & cols),
                        "missing_required_features": len(missing),
                        "extra_feature_columns": len(extra),
                        "has_record_id": "record_id" in cols,
                        "has_source_dataset": "source_dataset" in cols,
                        "nonempty": len(df) > 0,
                        "schema_exact_match": len(missing) == 0 and len(extra) == 0,
                    }
                )
                can_run = bool(row["schema_exact_match"] and row["has_record_id"] and row["has_source_dataset"] and row["nonempty"])
                row["can_run_multimodal_external_validation"] = can_run
                blockers = []
                if not row["nonempty"]:
                    blockers.append("external_structured_feature_table_empty")
                if not row["schema_exact_match"]:
                    blockers.append("external_structured_feature_schema_mismatch")
                if not row["has_record_id"]:
                    blockers.append("record_id_missing")
                if not row["has_source_dataset"]:
                    blockers.append("source_dataset_missing")
                row["blocking_issue"] = "" if can_run else ";".join(blockers)
            except Exception as exc:
                row["blocking_issue"] = f"external_structured_feature_table_unreadable:{exc}"
        rows.append(row)
    return pd.DataFrame(rows, columns=COLUMNS)


def _write_report(result: pd.DataFrame) -> None:
    text = "\n".join(
        [
            "# External Structured Feature Schema Validation Report",
            "",
            "Date: " + date.today().isoformat(),
            "",
            result.to_markdown(index=False),
            "",
            "A dataset is eligible for multimodal external validation only when the table is nonempty, has `record_id` and `source_dataset`, and exactly matches the frozen PTB-XL+ 531 structured feature schema.",
        ]
    )
    write_markdown("results/external/external_structured_feature_schema_validation_report.md", text + "\n")


def main() -> None:
    ensure_dir("results/external")
    ensure_dir("tables")
    result = validate()
    safe_to_csv(result, "tables/table_external_structured_feature_schema_validation.csv")
    _write_report(result)
    print("Wrote external structured feature schema validation report.")


if __name__ == "__main__":
    main()
