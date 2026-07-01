from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from src.utils.io import ensure_dir, safe_to_csv, write_markdown


MAPPING_PATH = Path("tables/table_ptbxl_plus_ecgdeli_feature_mapping_audit.csv")
DESCRIPTION_PATH = Path("data/raw/ptbxl_plus/features/feature_description.csv")


def _description_lookup(description: pd.DataFrame) -> dict[str, pd.Series]:
    lookup: dict[str, pd.Series] = {}
    for _, row in description.iterrows():
        feature_id = str(row.get("id", "")).strip()
        if not feature_id:
            continue
        lookup[feature_id] = row
        if feature_id.endswith("_X"):
            lookup[feature_id[: -len("_X")]] = row
        if feature_id.endswith("__Global"):
            lookup[feature_id[: -len("_Global")]] = row
    return lookup


def build_feature_description_audit() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    mapping = pd.read_csv(MAPPING_PATH)
    description = pd.read_csv(DESCRIPTION_PATH)
    lookup = _description_lookup(description)

    unresolved = mapping[mapping["derivability"].ne("direct_ecgdeli")].copy()
    rows = []
    for row in unresolved.to_dict(orient="records"):
        base_feature = str(row["base_feature"])
        desc = lookup.get(base_feature)
        description_found = desc is not None
        rows.append(
            {
                "ptbxl_plus_feature": row["ptbxl_plus_feature"],
                "base_feature": base_feature,
                "location": row["location"],
                "summary_statistic": row["summary_statistic"],
                "derivability": row["derivability"],
                "description_found": bool(description_found),
                "description_id": "" if desc is None else str(desc.get("id", "")),
                "ecgdeli_feature": "" if desc is None else str(desc.get("ecgdeli_feature", "")),
                "unit": "" if desc is None else str(desc.get("unit", "")),
                "description": "" if desc is None else str(desc.get("description", "")),
                "comment": "" if desc is None else str(desc.get("comment", "")),
                "recipe_status": "semantic_description_only" if description_found else "not_found_in_feature_description",
                "still_missing_for_exact_reproduction": (
                    "Exact beat inclusion, preprocessing, summary aggregation, missing-value handling, "
                    "and numeric agreement against official PTB-XL+ remain unresolved."
                ),
            }
        )

    audit = pd.DataFrame(rows)
    family_summary = (
        audit.groupby(["base_feature", "derivability", "description_found"], dropna=False)
        .agg(
            n_features=("ptbxl_plus_feature", "size"),
            example_description_id=("description_id", "first"),
            example_ecgdeli_feature=("ecgdeli_feature", "first"),
            example_description=("description", "first"),
        )
        .reset_index()
        .sort_values(["description_found", "base_feature"], ascending=[False, True])
    )
    decision = pd.DataFrame(
        [
            {
                "can_generate_exact_531_features": False,
                "can_run_multimodal_external_validation": False,
                "unresolved_feature_columns": int(len(audit)),
                "unresolved_columns_with_feature_description": int(audit["description_found"].sum()),
                "unresolved_columns_without_feature_description": int((~audit["description_found"]).sum()),
                "blocking_issue": "direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing",
                "notes": (
                    "feature_description.csv provides useful semantics for unresolved PTB-XL+ features, "
                    "but it does not resolve the exact aggregation recipe and does not explain the observed "
                    "numeric mismatch between local ECGdeli recomputation and official PTB-XL+ values."
                ),
            }
        ]
    )
    return audit, family_summary, decision


def _write_summary(audit: pd.DataFrame, family_summary: pd.DataFrame, decision: pd.DataFrame) -> None:
    documented = family_summary[family_summary["description_found"]].copy()
    text = "\n".join(
        [
            "# Stage 14J PTB-XL+ Feature Description Audit Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "The official PTB-XL+ feature description table was audited against the 111 frozen structured feature columns that remain outside the direct ECGdeli candidate set.",
            "",
            "This stage is documentation and recipe triage only. It does not generate external structured feature tables and does not unlock multimodal external validation.",
            "",
            "## Decision",
            "",
            decision.to_markdown(index=False),
            "",
            "## Unresolved Feature Families",
            "",
            family_summary.to_markdown(index=False),
            "",
            "## Documented But Still Not Reproducible",
            "",
            documented[["base_feature", "n_features", "example_description_id", "example_ecgdeli_feature", "example_description"]].to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- `feature_description.csv` confirms that several unresolved families have official semantic descriptions, including QT correction, P morphology, ST elevation, and electrical heart axis.",
            "- These descriptions identify expected feature concepts or ECGdeli-style names, but they do not define a complete waveform-to-531-column recipe.",
            "- Stage 14H/14I already showed that even the direct 420-feature subset does not numerically match official PTB-XL+ values closely enough to claim exact reproduction.",
            "- Therefore, external multimodal validation remains blocked until an exact PTB-XL+ feature-generation recipe is obtained or reconstructed and validated numerically.",
            "",
            "## Next Step",
            "",
            "Prepare a compact recipe-blocker package listing the exact missing definitions, numeric mismatch evidence, and the minimum requirements for unlocking external multimodal validation.",
        ]
    )
    write_markdown("results/stage14j_ptbxl_plus_feature_description_audit_summary.md", text + "\n")


def main() -> None:
    ensure_dir("tables")
    ensure_dir("results")
    audit, family_summary, decision = build_feature_description_audit()
    safe_to_csv(audit, "tables/table_ptbxl_plus_feature_description_unresolved_audit.csv")
    safe_to_csv(family_summary, "tables/table_ptbxl_plus_feature_description_family_summary.csv")
    safe_to_csv(decision, "tables/table_ptbxl_plus_feature_description_decision.csv")
    _write_summary(audit, family_summary, decision)
    print("Wrote PTB-XL+ feature description audit outputs.")


if __name__ == "__main__":
    main()
