from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, safe_to_csv, write_markdown


LEADS = {"I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"}
STATS = {"mean", "iqr", "count"}

DIRECT_LEADWISE = {
    "P_Amp": ("amplitude", "P wave amplitude", "Amplitude_feature_12leads(:,:,1)"),
    "Q_Amp": ("amplitude", "Q peak amplitude", "Amplitude_feature_12leads(:,:,2)"),
    "R_Amp": ("amplitude", "R peak amplitude", "Amplitude_feature_12leads(:,:,3)"),
    "S_Amp": ("amplitude", "S peak amplitude", "Amplitude_feature_12leads(:,:,4)"),
    "T_Amp": ("amplitude", "T wave amplitude", "Amplitude_feature_12leads(:,:,5)"),
    "P_DurFull": ("interval", "P wave duration", "Timing_feature_12leads(:,:,1)"),
    "QRS_Dur": ("interval", "QRS duration", "Timing_feature_12leads(:,:,2)"),
    "T_DurFull": ("interval", "T wave duration", "Timing_feature_12leads(:,:,3)"),
    "PQ_Int": ("interval", "PQ interval", "Timing_feature_12leads(:,:,4)"),
    "PR_Int": ("interval", "PR interval", "Timing_feature_12leads(:,:,5)"),
    "QT_Int": ("interval", "QT interval", "Timing_feature_12leads(:,:,6)"),
}

DIRECT_GLOBAL = {
    "P_Dur": ("interval_sync", "global P wave duration", "Timing_feature_sync(:,1)"),
    "QRS_Dur": ("interval_sync", "global QRS duration", "Timing_feature_sync(:,2)"),
    "T_Dur": ("interval_sync", "global T wave duration", "Timing_feature_sync(:,3)"),
    "PQ_Int": ("interval_sync", "global PQ interval", "Timing_feature_sync(:,4)"),
    "PR_Int": ("interval_sync", "global PR interval", "Timing_feature_sync(:,5)"),
    "QT_Int": ("interval_sync", "global QT interval", "Timing_feature_sync(:,6)"),
    "QT_IntFramingham": ("interval_sync", "global Framingham-corrected QT interval", "Timing_feature_sync(:,7)"),
    "RR_Mean": ("interval_sync", "global RR interval", "Timing_feature_sync(:,8)"),
}

EXTRA_FORMULA = {
    "QT_IntCorr": "leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule",
}

MORPHOLOGY = {
    "P_Morph": "Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed",
}

UNKNOWN = {
    "ST_Elev": "ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors",
    "HA_": "HA global feature definition is not available from audited ECGdeli functions",
}


def _split_stat(name: str) -> tuple[str, str]:
    if name.endswith("_iqr"):
        return name[: -len("_iqr")], "iqr"
    if name.endswith("_count"):
        return name[: -len("_count")], "count"
    return name, "mean"


def _split_base_location(core: str) -> tuple[str, str]:
    for location in sorted(LEADS | {"Global"}, key=len, reverse=True):
        suffix = "_" + location
        if core.endswith(suffix):
            return core[: -len(suffix)], location
    return core, ""


def classify_feature(name: str) -> dict[str, Any]:
    core, stat = _split_stat(name)
    base, location = _split_base_location(core)
    row: dict[str, Any] = {
        "ptbxl_plus_feature": name,
        "base_feature": base,
        "location": location,
        "summary_statistic": stat,
        "derivability": "unknown_recipe",
        "ecgdeli_source": "",
        "requires_exact_ptbxl_plus_rule": True,
        "notes": "",
    }
    if stat not in STATS:
        row["notes"] = "Unrecognized summary suffix."
        return row
    if location in LEADS and base in DIRECT_LEADWISE:
        kind, description, source = DIRECT_LEADWISE[base]
        row.update(
            {
                "derivability": "direct_ecgdeli",
                "ecgdeli_source": source,
                "requires_exact_ptbxl_plus_rule": True,
                "notes": f"Appears derivable from ECGdeli {kind}: {description}; exact filtering and aggregation must still match PTB-XL+.",
            }
        )
        return row
    if location == "Global" and base in DIRECT_GLOBAL:
        kind, description, source = DIRECT_GLOBAL[base]
        row.update(
            {
                "derivability": "direct_ecgdeli",
                "ecgdeli_source": source,
                "requires_exact_ptbxl_plus_rule": True,
                "notes": f"Appears derivable from ECGdeli {kind}: {description}; exact aggregation must still match PTB-XL+.",
            }
        )
        return row
    if location in LEADS and base in EXTRA_FORMULA:
        row.update(
            {
                "derivability": "requires_extra_formula",
                "ecgdeli_source": "Timing_feature_12leads(:,:,6) plus RR/correction formula",
                "notes": EXTRA_FORMULA[base],
            }
        )
        return row
    if location in LEADS and base in MORPHOLOGY:
        row.update(
            {
                "derivability": "requires_morphology_function",
                "ecgdeli_source": "Get_P_Morphology",
                "notes": MORPHOLOGY[base],
            }
        )
        return row
    for prefix, note in UNKNOWN.items():
        if base.startswith(prefix):
            row["notes"] = note
            return row
    row["notes"] = "No audited ECGdeli source rule identified."
    return row


def build_mapping() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = [line.strip() for line in Path("data/processed/structured_feature_names.txt").read_text().splitlines() if line.strip()]
    mapping = pd.DataFrame([classify_feature(name) for name in required])
    counts = Counter(mapping["derivability"])
    summary = pd.DataFrame(
        [
            {
                "derivability": key,
                "n_features": int(value),
                "percent_of_531": round(100.0 * value / len(mapping), 2),
            }
            for key, value in sorted(counts.items())
        ]
    )
    exact = False
    decision = pd.DataFrame(
        [
            {
                "can_generate_exact_531_features": exact,
                "can_run_multimodal_external_validation": False,
                "direct_or_formula_candidate_features": int(mapping["derivability"].isin(["direct_ecgdeli", "requires_extra_formula", "requires_morphology_function"]).sum()),
                "unknown_recipe_features": int(mapping["derivability"].eq("unknown_recipe").sum()),
                "blocking_issue": "ptbxl_plus_exact_531_recipe_missing",
                "notes": "This is a feature-name mapping audit only; it does not establish exact PTB-XL+ aggregation compatibility.",
            }
        ]
    )
    return mapping, summary, decision


def _write_summary(mapping: pd.DataFrame, summary: pd.DataFrame, decision: pd.DataFrame) -> None:
    examples = mapping.groupby("derivability").head(8)
    text = "\n".join(
        [
            "# Stage 14F PTB-XL+ ECGdeli Feature Mapping Audit Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "The frozen PTB-XL+ 531 structured feature names were parsed and compared against the audited ECGdeli MATLAB outputs: amplitude features, interval features, synchronized interval features, and P-wave morphology.",
            "",
            "This is a schema and recipe audit only. It does not generate exact PTB-XL+ external structured features.",
            "",
            "## Derivability Summary",
            "",
            summary.to_markdown(index=False),
            "",
            "## Decision",
            "",
            decision.to_markdown(index=False),
            "",
            "## Example Mappings",
            "",
            examples[["ptbxl_plus_feature", "derivability", "ecgdeli_source", "notes"]].to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- Many amplitude and interval feature names appear structurally derivable from ECGdeli outputs.",
            "- QT correction, P morphology, ST elevation, and HA features still require exact PTB-XL+ definitions or additional audited implementation rules.",
            "- Even direct candidates still require exact agreement on filtering, units, lead ordering, beat inclusion, summary statistics, and missing-value handling.",
            "- Therefore, full multimodal external validation remains blocked.",
            "",
            "## Next Step",
            "",
            "Implement a guarded candidate generator only for direct ECGdeli features, compare its columns against the frozen 531 schema, and leave unresolved columns missing until the exact PTB-XL+ recipe is obtained or faithfully reconstructed.",
        ]
    )
    write_markdown("results/stage14f_ptbxl_plus_feature_mapping_audit_summary.md", text + "\n")


def main() -> None:
    ensure_dir("tables")
    ensure_dir("results")
    mapping, summary, decision = build_mapping()
    safe_to_csv(mapping, "tables/table_ptbxl_plus_ecgdeli_feature_mapping_audit.csv")
    safe_to_csv(summary, "tables/table_ptbxl_plus_ecgdeli_feature_mapping_summary.csv")
    safe_to_csv(decision, "tables/table_ptbxl_plus_ecgdeli_feature_mapping_decision.csv")
    _write_summary(mapping, summary, decision)
    print("Wrote PTB-XL+ ECGdeli feature mapping audit outputs.")


if __name__ == "__main__":
    main()
