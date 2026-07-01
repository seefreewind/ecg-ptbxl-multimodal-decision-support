from __future__ import annotations

from datetime import date

import pandas as pd

from src.utils.io import ensure_dir, safe_to_csv, write_markdown


def _read_first(path: str) -> pd.Series:
    return pd.read_csv(path).iloc[0]


def build_recipe_blocker_package() -> tuple[pd.DataFrame, pd.DataFrame]:
    mapping_decision = _read_first("tables/table_ptbxl_plus_ecgdeli_feature_mapping_decision.csv")
    recompute_decision = _read_first("tables/table_ptbxl_ecgdeli_direct_recompute_decision.csv")
    discrepancy_decision = _read_first("tables/table_ptbxl_ecgdeli_direct_discrepancy_decision.csv")
    description_decision = _read_first("tables/table_ptbxl_plus_feature_description_decision.csv")

    requirements = pd.DataFrame(
        [
            {
                "requirement": "Complete exact 531-column PTB-XL+ waveform-to-feature recipe",
                "current_evidence": (
                    f"Stage 14F maps 420 direct candidates but leaves "
                    f"{int(mapping_decision['unknown_recipe_features'])} unknown-recipe columns plus formula/morphology columns."
                ),
                "minimum_unlock_condition": (
                    "All 531 frozen structured columns can be generated from external waveforms with documented formulas, units, "
                    "lead handling, summary statistics, and missing-value rules."
                ),
                "status": "blocked",
            },
            {
                "requirement": "Numeric agreement with official PTB-XL+ for direct ECGdeli candidates",
                "current_evidence": (
                    f"Stage 14H allclose direct features: "
                    f"{int(recompute_decision['n_direct_features_allclose'])}/"
                    f"{int(recompute_decision['n_direct_features_compared'])}; "
                    f"median feature MAE {float(recompute_decision['median_feature_mae']):.6f}."
                ),
                "minimum_unlock_condition": (
                    "A held-out PTB-XL recomputation audit shows near-exact agreement for direct features under a prespecified tolerance."
                ),
                "status": "blocked",
            },
            {
                "requirement": "Resolve T/QT interval discrepancy mechanism",
                "current_evidence": (
                    f"Stage 14I worst family is {discrepancy_decision['worst_family']}; "
                    f"{int(discrepancy_decision['families_with_any_discrepancy'])} families show at least one discrepancy."
                ),
                "minimum_unlock_condition": (
                    "Preprocessing, fiducial selection, beat inclusion, interval definition, and aggregation choices explain and remove the mismatch."
                ),
                "status": "blocked",
            },
            {
                "requirement": "Implement QT_IntCorr, P_Morph, ST_Elev, and HA__Global rules",
                "current_evidence": (
                    f"Stage 14J finds semantic descriptions for "
                    f"{int(description_decision['unresolved_columns_with_feature_description'])}/"
                    f"{int(description_decision['unresolved_feature_columns'])} unresolved columns, but not an executable recipe."
                ),
                "minimum_unlock_condition": (
                    "Each unresolved family has executable code and numeric validation against official PTB-XL+ examples."
                ),
                "status": "blocked",
            },
            {
                "requirement": "Generate nonempty external 531-column structured feature tables",
                "current_evidence": (
                    "Stage 14C schema gate still reports missing official external structured tables; "
                    "Stage 14G candidate files intentionally contain only 420 direct feature columns."
                ),
                "minimum_unlock_condition": (
                    "data/processed/external/cpsc2018_structured_features.csv and "
                    "data/processed/external/chapman_structured_features.csv exist, are nonempty, and exactly match the frozen PTB-XL+ schema."
                ),
                "status": "blocked",
            },
            {
                "requirement": "Keep candidate/prototype files separate from official multimodal inputs",
                "current_evidence": (
                    "Stage 14E prototype and Stage 14G direct-candidate files are useful engineering evidence but are incomplete."
                ),
                "minimum_unlock_condition": (
                    "Only exact 531-column validated files are registered as external structured features; prototype/candidate files remain excluded."
                ),
                "status": "blocked",
            },
        ]
    )

    decision = pd.DataFrame(
        [
            {
                "can_claim_exact_ptbxl_plus_reproduction": False,
                "can_run_multimodal_external_validation": False,
                "n_blocked_requirements": int(len(requirements)),
                "blocking_issue": "direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing",
                "allowed_next_step": "obtain_or_reconstruct_exact_ptbxl_plus_recipe_then_rerun_schema_and_numeric_validation",
            }
        ]
    )
    return requirements, decision


def _write_package(requirements: pd.DataFrame, decision: pd.DataFrame) -> None:
    text = "\n".join(
        [
            "# Stage 14K PTB-XL+ Recipe Blocker Package",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Purpose",
            "",
            "This package defines the exact blocker for external multimodal validation. It separates validated progress from unresolved PTB-XL+ feature-reconstruction requirements.",
            "",
            "It does not generate structured feature tables, does not run multimodal external validation, and does not change the external schema gate.",
            "",
            "## Decision",
            "",
            decision.to_markdown(index=False),
            "",
            "## Unlock Requirements",
            "",
            requirements.to_markdown(index=False),
            "",
            "## Current Evidence",
            "",
            "- MATLAB R2025a and official ECGdeli are callable, and the ECGdeli smoke test passes.",
            "- External WFDB records from CPSC2018 and Chapman-Shaoxing can enter the ECGdeli extraction path.",
            "- A 420-column direct candidate generator works technically, but its PTB-XL recomputation does not numerically match official PTB-XL+ values closely enough.",
            "- The remaining 111 frozen PTB-XL+ columns have semantic descriptions, but semantic descriptions are not a full executable recipe.",
            "",
            "## Practical Consequence",
            "",
            "Only signal-only external validation is currently supportable. Fair concat or gated multimodal external validation must wait until exact 531-column external structured tables pass both schema validation and numeric sanity checks.",
            "",
            "## Minimum Evidence Needed To Proceed",
            "",
            "1. Exact PTB-XL+ feature-generation code or a faithful reconstruction of it.",
            "2. A PTB-XL internal recomputation audit showing numeric agreement with official PTB-XL+ feature values.",
            "3. Nonempty CPSC2018 and Chapman-Shaoxing external structured feature tables with the frozen 531-column schema.",
            "4. A passing Stage 14C schema gate before any external fair concat or gated fusion evaluation.",
        ]
    )
    write_markdown("results/stage14k_ptbxl_plus_recipe_blocker_package.md", text + "\n")


def main() -> None:
    ensure_dir("tables")
    ensure_dir("results")
    requirements, decision = build_recipe_blocker_package()
    safe_to_csv(requirements, "tables/table_ptbxl_plus_recipe_unlock_requirements.csv")
    safe_to_csv(decision, "tables/table_ptbxl_plus_recipe_blocker_decision.csv")
    _write_package(requirements, decision)
    print("Wrote PTB-XL+ recipe blocker package.")


if __name__ == "__main__":
    main()
