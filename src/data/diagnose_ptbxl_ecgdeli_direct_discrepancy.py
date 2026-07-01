from __future__ import annotations

from datetime import date

import pandas as pd

from src.data.audit_ptbxl_plus_ecgdeli_feature_mapping import _split_base_location, _split_stat
from src.utils.io import ensure_dir, safe_to_csv, write_markdown


def diagnose() -> tuple[pd.DataFrame, pd.DataFrame]:
    comparison = pd.read_csv("tables/table_ptbxl_ecgdeli_direct_recompute_comparison.csv")
    rows = []
    for _, row in comparison.iterrows():
        core, stat = _split_stat(str(row["feature"]))
        base, location = _split_base_location(core)
        rows.append({**row.to_dict(), "base_feature": base, "location": location, "summary_statistic": stat})
    annotated = pd.DataFrame(rows)
    grouped = (
        annotated.groupby(["base_feature", "summary_statistic"], as_index=False)
        .agg(
            n_features=("feature", "count"),
            n_pairs=("n_pairs", "sum"),
            n_allclose=("allclose_atol_1e_6", "sum"),
            median_mean_abs_error=("mean_abs_error", "median"),
            max_mean_abs_error=("mean_abs_error", "max"),
            median_max_abs_error=("max_abs_error", "median"),
        )
        .sort_values(["median_mean_abs_error", "max_mean_abs_error"], ascending=False)
    )
    grouped["allclose_rate"] = grouped["n_allclose"] / grouped["n_features"]
    return annotated, grouped


def _decision(grouped: pd.DataFrame) -> pd.DataFrame:
    exact_enough = bool((grouped["allclose_rate"] == 1.0).all())
    worst = grouped.sort_values("median_mean_abs_error", ascending=False).head(1)
    worst_label = "" if worst.empty else f"{worst.iloc[0]['base_feature']}:{worst.iloc[0]['summary_statistic']}"
    return pd.DataFrame(
        [
            {
                "direct_420_exact_enough_for_recipe_claim": exact_enough,
                "can_run_multimodal_external_validation": False,
                "worst_family": worst_label,
                "families_with_any_discrepancy": int((grouped["allclose_rate"] < 1.0).sum()),
                "blocking_issue": "direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing",
                "notes": "Direct candidate feature names are not sufficient; numeric definitions and remaining 111 features still need exact reconstruction.",
            }
        ]
    )


def _write_summary(annotated: pd.DataFrame, grouped: pd.DataFrame, decision: pd.DataFrame) -> None:
    worst_features = annotated.sort_values("mean_abs_error", ascending=False).head(20)
    text = "\n".join(
        [
            "# Stage 14I PTB-XL ECGdeli Direct Discrepancy Diagnosis Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "The Stage 14H direct-feature recomputation audit was grouped by ECG feature family and summary statistic to identify where local ECGdeli-derived values diverge most from official PTB-XL+ `ecgdeli_features.csv`.",
            "",
            "## Decision",
            "",
            decision.to_markdown(index=False),
            "",
            "## Family-Level Discrepancy Summary",
            "",
            grouped.to_markdown(index=False),
            "",
            "## Largest Individual Feature Differences",
            "",
            worst_features[["feature", "base_feature", "location", "summary_statistic", "n_pairs", "mean_abs_error", "median_abs_error", "max_abs_error", "allclose_atol_1e_6"]].to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- Count columns are much closer than value columns, suggesting beat counts often align while interval/amplitude definitions or aggregation differ.",
            "- T-duration and QT-related direct features show the largest discrepancies in the small PTB-XL audit sample.",
            "- Feature names alone are insufficient for exact PTB-XL+ reproduction.",
            "- Multimodal external validation remains blocked.",
            "",
            "## Next Step",
            "",
            "Prioritize exact reconstruction of ECGdeli preprocessing, fiducial definitions, summary statistics, and T/QT interval definitions before attempting to fill the remaining external 531-column schema.",
        ]
    )
    write_markdown("results/stage14i_ptbxl_ecgdeli_direct_discrepancy_diagnosis_summary.md", text + "\n")


def main() -> None:
    ensure_dir("tables")
    ensure_dir("results")
    annotated, grouped = diagnose()
    decision = _decision(grouped)
    safe_to_csv(annotated, "tables/table_ptbxl_ecgdeli_direct_discrepancy_annotated_features.csv")
    safe_to_csv(grouped, "tables/table_ptbxl_ecgdeli_direct_discrepancy_by_family.csv")
    safe_to_csv(decision, "tables/table_ptbxl_ecgdeli_direct_discrepancy_decision.csv")
    _write_summary(annotated, grouped, decision)
    print("Wrote PTB-XL ECGdeli direct discrepancy diagnosis outputs.")


if __name__ == "__main__":
    main()
