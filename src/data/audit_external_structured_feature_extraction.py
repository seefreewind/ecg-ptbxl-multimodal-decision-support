from __future__ import annotations

import importlib.util
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


AUDIT_COLUMNS = [
    "dataset",
    "required_feature_count",
    "existing_external_feature_table",
    "existing_feature_count",
    "exact_ptbxl_plus_feature_match",
    "missing_required_features",
    "ecgdeli_python_available",
    "ecgdeli_cli_available",
    "ecgdeli_r_available",
    "neurokit2_available",
    "can_generate_exact_ptbxl_plus_features_now",
    "can_run_full_multimodal_external_validation",
    "recommended_action",
    "blocking_issue",
]


def _required_features() -> list[str]:
    path = Path("data/processed/structured_feature_names.txt")
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def _external_roots() -> dict[str, Path]:
    cfg = load_yaml("configs/data_external.yaml")
    return {dataset: Path(cfg["external"][dataset]["root_dir"]) for dataset in ["cpsc2018", "chapman"]}


def _feature_candidates(root: Path) -> list[Path]:
    if not root.exists():
        return []
    suffixes = {".csv", ".tsv", ".parquet", ".feather", ".pkl", ".pickle"}
    tokens = ["feature", "ecgdeli", "structured", "12sl", "unig"]
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in suffixes
        and any(token in path.name.lower() for token in tokens)
    ]


def _read_columns(path: Path) -> set[str]:
    if path.suffix.lower() == ".csv":
        return set(map(str, pd.read_csv(path, nrows=1).columns))
    if path.suffix.lower() == ".tsv":
        return set(map(str, pd.read_csv(path, sep="\t", nrows=1).columns))
    if path.suffix.lower() in {".parquet", ".feather"}:
        return set(map(str, pd.read_parquet(path).head(1).columns))
    return set(map(str, pd.read_pickle(path).head(1).columns))


def _r_package_available(name: str) -> bool:
    rscript = shutil.which("Rscript")
    if not rscript:
        return False
    try:
        out = subprocess.run(
            [rscript, "-e", f'cat(requireNamespace("{name}", quietly=TRUE))'],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return False
    return "TRUE" in out.stdout


def audit() -> pd.DataFrame:
    required = _required_features()
    required_set = set(required)
    ecgdeli_python = importlib.util.find_spec("ecgdeli") is not None
    neurokit2 = importlib.util.find_spec("neurokit2") is not None
    ecgdeli_cli = shutil.which("ecgdeli") is not None
    ecgdeli_r = _r_package_available("ecgdeli")
    rows: list[dict[str, Any]] = []
    for dataset, root in _external_roots().items():
        best_path = ""
        best_present = 0
        best_missing = len(required)
        exact = False
        for candidate in _feature_candidates(root):
            try:
                cols = _read_columns(candidate)
            except Exception:
                continue
            present = len(required_set & cols)
            missing = len(required_set - cols)
            if present > best_present:
                best_path = str(candidate)
                best_present = present
                best_missing = missing
                exact = missing == 0
        can_generate = bool((ecgdeli_python or ecgdeli_cli or ecgdeli_r) and root.exists())
        can_multimodal = bool(exact)
        if exact:
            action = "run_full_multimodal_external_validation"
            blocker = ""
        elif can_generate:
            action = "run_exact_ecgdeli_feature_extraction_then_reaudit"
            blocker = "exact_external_features_not_yet_generated"
        else:
            action = "install_or_configure_exact_ecgdeli_feature_extraction_pipeline"
            blocker = "ecgdeli_compatible_feature_pipeline_missing"
        rows.append(
            {
                "dataset": dataset,
                "required_feature_count": len(required),
                "existing_external_feature_table": best_path,
                "existing_feature_count": best_present,
                "exact_ptbxl_plus_feature_match": exact,
                "missing_required_features": best_missing,
                "ecgdeli_python_available": ecgdeli_python,
                "ecgdeli_cli_available": ecgdeli_cli,
                "ecgdeli_r_available": ecgdeli_r,
                "neurokit2_available": neurokit2,
                "can_generate_exact_ptbxl_plus_features_now": can_generate,
                "can_run_full_multimodal_external_validation": can_multimodal,
                "recommended_action": action,
                "blocking_issue": blocker,
            }
        )
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def _write_templates(required: list[str]) -> None:
    out_dir = ensure_dir("data/processed/external")
    (out_dir / "external_structured_feature_template_columns.txt").write_text("\n".join(required) + "\n")
    columns = ["record_id", "source_dataset"] + required
    for dataset in ["cpsc2018", "chapman"]:
        safe_to_csv(pd.DataFrame(columns=columns), out_dir / f"{dataset}_structured_features_template.csv")


def _write_reports(audit_df: pd.DataFrame) -> None:
    report = "\n".join(
        [
            "# External Structured Feature Extraction Audit",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Audit Table",
            "",
            audit_df.to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "Full multimodal external validation remains blocked unless external structured features exactly match the PTB-XL+ selected 531 ecgdeli feature names and definitions.",
            "",
            "NeuroKit2-style features may be useful for a separate exploratory model, but they are not treated as compatible with the frozen fair concat or gated fusion models.",
        ]
    )
    write_markdown("results/external/external_structured_feature_extraction_audit.md", report + "\n")
    summary = "\n".join(
        [
            "# Stage 14A External Structured Feature Extraction Readiness Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "Stage 14A completed as a readiness audit. No external structured features were fabricated and no multimodal external validation was run.",
            "",
            "## Result",
            "",
            audit_df.to_markdown(index=False),
            "",
            "## Key Conclusion",
            "",
            "`external_structured_features_missing_for_multimodal` remains unresolved. The project cannot run fair concat or gated fusion on external datasets until an exact PTB-XL+ ecgdeli-compatible feature extraction pipeline is installed and validated.",
            "",
            "## Generated Templates",
            "",
            "- `data/processed/external/external_structured_feature_template_columns.txt`",
            "- `data/processed/external/cpsc2018_structured_features_template.csv`",
            "- `data/processed/external/chapman_structured_features_template.csv`",
            "",
            "## Next Step",
            "",
            "Install/configure an exact ecgdeli-compatible extractor or obtain external feature tables with the same 531 PTB-XL+ feature columns, then rerun this audit before multimodal external validation.",
        ]
    )
    write_markdown("results/stage14a_external_structured_feature_summary.md", summary + "\n")


def main() -> None:
    ensure_dir("results/external")
    ensure_dir("tables")
    required = _required_features()
    audit_df = audit()
    safe_to_csv(audit_df, "tables/table_external_structured_feature_extraction_audit.csv")
    _write_templates(required)
    _write_reports(audit_df)
    print("Wrote external structured feature extraction audit and templates.")


if __name__ == "__main__":
    main()
