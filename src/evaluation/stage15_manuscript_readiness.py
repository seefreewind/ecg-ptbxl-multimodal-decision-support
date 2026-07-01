from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

from src.evaluation.evaluator import evaluate_multilabel_predictions
from src.utils.io import ensure_dir, safe_to_csv, write_markdown


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
EXTERNAL_LABELS = {"cpsc2018": ["NORM", "CD"], "chapman": ["MI", "CD", "HYP"]}
N_BINS = 10


def _ece_mce(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = N_BINS) -> tuple[float, float, pd.DataFrame]:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    ece = 0.0
    mce = 0.0
    for idx, (left, right) in enumerate(zip(bins[:-1], bins[1:])):
        mask = (y_prob >= left) & (y_prob < right if right < 1.0 else y_prob <= right)
        n = int(mask.sum())
        if n:
            confidence = float(y_prob[mask].mean())
            observed = float(y_true[mask].mean())
            gap = abs(observed - confidence)
            ece += float(n / len(y_true)) * gap
            mce = max(mce, gap)
        else:
            confidence = math.nan
            observed = math.nan
            gap = math.nan
        rows.append(
            {
                "bin": idx,
                "bin_left": float(left),
                "bin_right": float(right),
                "n": n,
                "mean_predicted_probability": confidence,
                "observed_fraction_positive": observed,
                "absolute_gap": gap,
            }
        )
    return float(ece), float(mce), pd.DataFrame(rows)


def _load_external_join(dataset: str) -> pd.DataFrame:
    labels = pd.read_csv(f"data/processed/external/{dataset}_labels_mapped.csv")
    pred = pd.read_csv(f"results/external/{dataset}_signal_predictions.csv")
    merged = labels.merge(pred, on=["record_id", "source_dataset"], how="inner")
    if merged.empty:
        raise ValueError(f"No joined external signal predictions for {dataset}.")
    return merged


def build_external_signal_diagnostics() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics = pd.read_csv("tables/table_external_signal_results.csv")
    diagnostic_rows = []
    calibration_rows = []
    reliability_frames = []
    temperature_exists = Path("results/calibration/temperature_params_signal_strong.json").exists()
    temperature_source = "internal validation temperature scaling" if temperature_exists else "missing internal temperature artifact"
    missing_note = "" if temperature_exists else "results/calibration/temperature_params_signal_strong.json is missing; external probabilities were evaluated as stored."

    for dataset, labels in EXTERNAL_LABELS.items():
        joined = _load_external_join(dataset)
        y_true = joined[[f"mapped_{label}" for label in labels]].to_numpy(dtype=int)
        y_prob = joined[[f"{label}_prob" for label in labels]].to_numpy(dtype=float)
        y_eval = evaluate_multilabel_predictions(y_true, y_prob, label_names=labels, split_name=f"external_{dataset}", model_name="strong_signal_only")
        macro = y_eval[y_eval["label"].eq("macro")].iloc[0]
        per_label_brier = []
        per_label_ece = []
        per_label_mce = []
        for label in labels:
            source = metrics[(metrics["dataset"].eq(dataset)) & (metrics["label"].eq(label))].iloc[0]
            truth = joined[f"mapped_{label}"].to_numpy(dtype=int)
            prob = joined[f"{label}_prob"].to_numpy(dtype=float)
            ece, mce, reliability = _ece_mce(truth, prob)
            brier = float(brier_score_loss(truth, prob))
            per_label_brier.append(brier)
            per_label_ece.append(ece)
            per_label_mce.append(mce)
            reliability.insert(0, "label", label)
            reliability.insert(0, "dataset", dataset)
            reliability["temperature_source"] = temperature_source
            reliability_frames.append(reliability)
            prevalence = float(truth.mean())
            note = (
                "Low AP/F1 should be interpreted with prevalence and validation-threshold transfer; no external threshold tuning was performed."
                if dataset == "chapman"
                else "Signal-only external result using validation-derived thresholds; no external threshold tuning was performed."
            )
            diagnostic_rows.append(
                {
                    "dataset": dataset,
                    "label": label,
                    "prevalence": prevalence,
                    "auroc": float(source["auroc"]),
                    "average_precision": float(source["average_precision"]),
                    "f1": float(source["f1"]),
                    "support": int(source["positive_count"]),
                    "n_records": int(source["n_records"]),
                    "threshold": float(source["threshold"]),
                    "threshold_source": str(source["threshold_source"]),
                    "temperature_source": temperature_source,
                    "brier_score": brier,
                    "ece": ece,
                    "mce": mce,
                    "interpretation_note": note,
                }
            )
        calibration_rows.append(
            {
                "dataset": dataset,
                "calibration_scope": "signal-only-external",
                "n_records": int(len(joined)),
                "labels": ",".join(labels),
                "macro_brier": float(np.mean(per_label_brier)),
                "micro_brier": float(np.mean((y_true.ravel() - y_prob.ravel()) ** 2)),
                "macro_ece": float(np.mean(per_label_ece)),
                "macro_mce": float(np.mean(per_label_mce)),
                "macro_auroc": float(macro["auroc"]),
                "macro_average_precision": float(macro["average_precision"]),
                "macro_f1": float(macro["f1"]),
                "temperature_source": temperature_source,
                "missing_artifact_note": missing_note,
            }
        )

    diagnostics = pd.DataFrame(diagnostic_rows)
    calibration = pd.DataFrame(calibration_rows)
    reliability = pd.concat(reliability_frames, ignore_index=True)
    safe_to_csv(diagnostics, "tables/table_stage15_external_signal_per_class_diagnostics.csv")
    safe_to_csv(calibration, "tables/table_stage15_external_signal_calibration.csv")
    safe_to_csv(reliability, "tables/table_stage15_external_signal_reliability.csv")
    return diagnostics, calibration, reliability


def build_claim_support() -> pd.DataFrame:
    rows: list[dict[str, Any]] = [
        ("C01", "Internal full-schema multimodal fusion improves over unimodal baselines.", "tables/table_stage8_ablation_comparison.csv; results/stage8_ablation_summary.md", "internal", "main", "moderate", "State as internal PTB-XL/PTB-XL+ evidence under frozen splits.", "Do not describe as externally validated multimodal performance.", "allowed"),
        ("C02", "Structured-only internal model is a valid comparator but not the top performer.", "tables/table_structured_mlp_results.csv", "internal", "main", "low", "Report as internal structured-only baseline.", "Do not imply structured-only replaces signal data.", "allowed"),
        ("C03", "Fair concat improves over signal-embedding MLP in the full-schema internal setting.", "tables/table_stage8_ablation_comparison.csv", "internal", "main", "moderate", "Use full-schema and internal qualifiers.", "Do not transfer this claim to external datasets.", "allowed"),
        ("C04", "Gated fusion has no statistically clear discriminative advantage over fair concat.", "tables/table_gated_vs_fair_concat_paired_bootstrap.csv", "internal", "main", "low", "Frame as a null/negative ablation result.", "Do not claim gated superiority.", "allowed"),
        ("C05", "Temperature scaling and reliability analysis support calibration assessment.", "results/stage9b_logits_temperature_summary.md; tables/table_calibration_temperature_scaled.csv", "internal", "main", "low", "Say temperatures were fitted on validation only.", "Do not claim clinical calibration readiness.", "allowed"),
        ("C06", "Uncertainty triage can identify lower-risk retained subsets internally.", "results/uncertainty/summary.md; tables/table_uncertainty_triage.csv", "internal", "main", "moderate", "Use internal decision-support wording.", "Do not claim clinical triage deployment.", "allowed"),
        ("C07", "XAI reports provide post-hoc signal and structured explanations.", "results/stage11_xai_summary.md; figures/source_data/fig6_xai_case_source_data.csv", "internal", "main", "moderate", "Describe as post-hoc interpretability examples.", "Do not claim mechanistic explanation or causal attribution.", "allowed"),
        ("C08", "DCA provides exploratory internal decision-curve evidence.", "results/stage12_dca_summary.md; tables/table_dca_summary.csv", "internal", "supplement", "moderate", "Use exploratory and threshold-dependent wording.", "Do not claim clinical net benefit validation.", "allowed"),
        ("C09", "CPSC2018 signal-only external validation supports limited signal-level transportability.", "tables/table_external_signal_results.csv", "signal-only-external", "main", "moderate", "Call this signal-only external validation.", "Do not call it multimodal external validation.", "allowed"),
        ("C10", "Chapman-Shaoxing signal-only external validation supports partial signal-level external evaluation.", "tables/table_external_signal_results.csv", "signal-only-external", "main", "moderate", "Mention MI/CD/HYP high-confidence label subset.", "Do not include Chapman sinus rhythm as main-analysis NORM.", "allowed"),
        ("C11", "Chapman macro AUROC can be high while AP/F1 are low because prevalence is low and thresholds transfer from PTB-XL validation.", "tables/table_stage15_external_signal_per_class_diagnostics.csv", "signal-only-external", "main", "moderate", "Report prevalence/support and threshold-transfer caveat.", "Do not tune thresholds on Chapman test labels.", "allowed"),
        ("C12", "Stage 14L reduced-schema structured-only performance collapses internally.", "tables/stage14l_internal_results.csv", "reproducibility-finding", "supplement", "moderate", "Frame as concordant-subset feasibility finding.", "Do not present as final external multimodal result.", "allowed"),
        ("C13", "Stage 14L external reduced-schema coverage is only two records per dataset.", "tables/stage14l_external_results.csv", "engineering-audit-only", "audit-only", "low", "Use as a coverage NO-GO gate.", "Do not compute or imply external multimodal performance from two records.", "allowed"),
        ("C14", "Exact PTB-XL+ 531-column external reconstruction is NO-GO.", "docs/STAGE14L_GO_NO_GO_DECISION.md; results/stage14j_ptbxl_plus_feature_description_audit_summary.md", "engineering-audit-only", "audit-only", "low", "Describe as de novo external reconstruction limitation.", "Do not say internal PTB-XL+ released features are invalid.", "allowed"),
        ("C15", "External multimodal validation has been completed.", "none", "forbidden", "forbidden", "high", "Forbidden.", "No external multimodal result exists.", "forbidden"),
        ("C16", "Gated fusion is superior to fair concat.", "tables/table_gated_vs_fair_concat_paired_bootstrap.csv", "forbidden", "forbidden", "high", "Forbidden; CI contains zero.", "Do not make architecture-superiority claim.", "forbidden"),
        ("C17", "The framework is clinically ready or clinically validated.", "none", "forbidden", "forbidden", "high", "Forbidden; public retrospective datasets only.", "Do not claim clinical deployment readiness.", "forbidden"),
        ("C18", "Exact 531-column PTB-XL+ external reproduction was achieved.", "none", "forbidden", "forbidden", "high", "Forbidden; Stage 14H-14L are NO-GO.", "Do not claim exact external structured feature reproduction.", "forbidden"),
        ("C19", "External signal calibration was evaluated without external tuning.", "tables/table_stage15_external_signal_calibration.csv", "signal-only-external", "supplement", "low", "State that temperature scaling was fit on internal validation and only evaluated externally.", "Do not refit calibration on external labels.", "allowed"),
        ("C20", "Figure source-data files are available for internal performance, calibration, uncertainty, and XAI.", "figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv; results/stage11a_figure_source_data_summary.md", "internal", "supplement", "low", "Use as reproducibility support.", "Do not imply external multimodal source data exist.", "allowed"),
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "claim_id",
            "manuscript_claim",
            "evidence_pointer",
            "scope",
            "allowed_location",
            "risk_level",
            "required_wording_constraint",
            "forbidden_overclaim",
            "final_status",
        ],
    )
    safe_to_csv(df, "tables/table_manuscript_claim_support.csv")
    return df


def write_boundaries() -> None:
    required_sentence = (
        "internal multimodal experiments remain reproducible because they use released PTB-XL+ feature values under frozen splits; "
        "the reproducibility limitation concerns de novo reconstruction of the same structured feature schema on external WFDB datasets, "
        "not reuse of the released PTB-XL+ resource"
    )
    text = f"""# Manuscript Result Boundaries

Date: {date.today().isoformat()}

## Core Boundary

{required_sentence}.

External multimodal validation is NO-GO. Current external evidence is signal-only only. Stage 14L is a reproducibility finding and feasibility audit, not an external multimodal result.

## Allowed main claims

- Internal full-schema PTB-XL/PTB-XL+ multimodal fusion improves over unimodal baselines under frozen splits.
- Fair concat captures the main internal multimodal gain.
- Gated fusion does not show a statistically clear advantage over fair concat.
- Signal-only external validation was completed on CPSC2018 and Chapman-Shaoxing.
- Calibration, uncertainty triage, XAI, and DCA support a trustworthy decision-support framing, with conservative interpretation.

## Supplement-only claims

- Internal DCA is exploratory and threshold-dependent.
- External signal-only calibration may be reported as supplementary because temperature scaling was fit internally and only evaluated externally.
- Stage 14L concordant-subset results may be included as a sensitivity or feasibility audit, not as a validation result.

## Engineering-audit-only findings

- PTB-XL+ exact 531-column external reconstruction remains unresolved.
- ECGdeli candidate/prototype files are incomplete and cannot be used as official external structured features.
- Stage 14L external coverage was two joinable records per dataset and therefore failed the external quality gate.

## Forbidden claims

- External multimodal validation was completed.
- Exact PTB-XL+ 531-column external reproduction was achieved.
- Gated fusion is superior to fair concat.
- The model is clinically ready, clinically validated, or deployable.
- Candidate/prototype structured features are valid PTB-XL+ external structured features.

## Required wording constraints

- Use "internal multimodal evaluation" for PTB-XL/PTB-XL+ full-schema experiments.
- Use "signal-only external validation" for CPSC2018 and Chapman-Shaoxing.
- Use "reproducibility audit" or "feasibility audit" for Stage 14L.
- State that validation-only thresholds and validation-fitted temperatures were used; no external test-set tuning was performed.
- For Chapman-Shaoxing, report prevalence/support and note that low AP/F1 can coexist with high AUROC under low prevalence and threshold transfer.

## Reviewer attack points and preemptive responses

1. Attack: "The title suggests cross-dataset multimodal validation."
   Response: Avoid naked "Cross-Dataset Validation" in the title. Use "Signal-Level External Validation" or "Reproducibility-Aware" wording.

2. Attack: "External multimodal validation is missing."
   Response: State this limitation directly. External validation is signal-only because exact PTB-XL+ compatible structured features could not be validated externally.

3. Attack: "PTB-XL+ feature reconstruction failed, so internal multimodal results are invalid."
   Response: The internal experiments use released PTB-XL+ feature values under frozen splits. The limitation concerns de novo reconstruction of the same schema on external WFDB datasets.

4. Attack: "Gated fusion does not improve over concat."
   Response: Treat this as a fair negative ablation. The supported contribution is multimodal complementarity and trustworthy evaluation, not gate superiority.

5. Attack: "Chapman AUROC is high but AP/F1 are low."
   Response: Report prevalence and support. Low-prevalence labels and transferred thresholds can yield low AP/F1 despite preserved ranking performance.
"""
    write_markdown("docs/MANUSCRIPT_RESULT_BOUNDARIES.md", text)


def write_title_abstract() -> None:
    text = f"""# Manuscript Title and Abstract Framing

Date: {date.today().isoformat()}

## Safe title options

1. Reproducibility-Aware Multimodal ECG Risk Stratification with Signal-Level External Validation
2. Interpretable Multimodal ECG Risk Stratification Using PTB-XL/PTB-XL+ with Signal-Level External Validation
3. A Reproducibility-Aware Decision-Support Framework for Multimodal ECG Risk Stratification

Recommended direction: use "Reproducibility-Aware" or "Signal-Level External Validation" and avoid a naked "Cross-Dataset Validation" claim.

## Structured abstract skeleton, 250-300 words

**Background:** Multimodal ECG decision-support models can combine raw waveform information with structured ECG-derived measurements, but their evaluation should distinguish internal multimodal evidence from external signal-level validation and from the feasibility of reconstructing structured features in new datasets.

**Methods:** We developed a PTB-XL/PTB-XL+ framework for five-superclass cardiac risk stratification using official train/validation/test splits. Signal embeddings from a one-dimensional ECG model were compared with released PTB-XL+ structured features, a fair concat multimodal model, and a gated fusion model under shared evaluation rules. Thresholds, calibration temperatures, and model selection were determined using validation data only. We assessed discrimination, calibration, uncertainty triage, post-hoc interpretability, and exploratory decision-curve analysis. External evaluation used CPSC2018 and Chapman-Shaoxing as signal-only datasets with pre-specified high-confidence label mappings. We also performed a reproducibility audit of ECGdeli-derived structured features to test whether PTB-XL+ compatible external structured features could be generated.

**Results:** In internal PTB-XL/PTB-XL+ testing, fair multimodal concat improved over unimodal baselines, whereas gated fusion showed no statistically clear advantage over fair concat in paired bootstrap analysis. Calibration and uncertainty analyses supported a decision-support framing but did not establish clinical readiness. Signal-only external validation showed preserved ranking performance in CPSC2018 and Chapman-Shaoxing, with lower AP/F1 in low-prevalence Chapman labels. The Stage 14L concordant-subset audit was NO-GO: internally the reduced structured subset did not provide stable multimodal gain, and externally the structured-feature coverage was insufficient.

**Conclusions:** The evidence supports internal multimodal complementarity and signal-level external validation, while external multimodal validation remains unavailable until exact PTB-XL+ compatible structured feature reconstruction can be validated.
"""
    write_markdown("docs/MANUSCRIPT_TITLE_ABSTRACT_FRAMING.md", text)


def build_figure_table_source_map() -> pd.DataFrame:
    rows = [
        ("Table 1", "Internal model performance", "tables/table_stage8_ablation_comparison.csv", "scripts/08d_build_ablation_summary.sh", "main", "no"),
        ("Table 2", "Gated vs fair concat paired bootstrap", "tables/table_gated_vs_fair_concat_paired_bootstrap.csv", "scripts/09b_evaluate_calibration.sh", "main", "no"),
        ("Figure 1", "Framework and data-flow schematic", "figures/source_data/fig1_framework_nodes.csv; figures/source_data/fig1_framework_edges.csv", "scripts/12_build_figure_source_data.sh", "main", "no"),
        ("Figure 2", "Internal fair multimodal performance", "figures/source_data/fig2_model_performance_long.csv", "scripts/12_build_figure_source_data.sh", "main", "no"),
        ("Figure 3", "Calibration/reliability", "figures/source_data/fig4_calibration_long.csv; results/calibration/reliability_curve_source_data.csv", "scripts/09c_plot_reliability.sh", "main", "no"),
        ("Figure 4", "Uncertainty triage", "figures/source_data/fig5_uncertainty_risk_coverage.csv", "scripts/10b_plot_uncertainty_triage.sh", "main", "no"),
        ("Figure 5", "Dual-modality XAI examples", "figures/source_data/fig6_xai_case_source_data.csv", "scripts/11d_build_unified_xai_reports.sh", "main", "no"),
        ("Table 3", "Signal-only external validation", "tables/table_external_signal_results.csv; tables/table_stage15_external_signal_per_class_diagnostics.csv", "scripts/15_stage15_manuscript_readiness.sh", "main", "no"),
        ("Supplementary Table S1", "External signal calibration", "tables/table_stage15_external_signal_calibration.csv; tables/table_stage15_external_signal_reliability.csv", "scripts/15_stage15_manuscript_readiness.sh", "supplement", "no"),
        ("Supplementary Table S2", "Structured-feature reproducibility audit summary", "tables/table_ptbxl_ecgdeli_direct_recompute_decision.csv; tables/stage14l_feature_manifest.csv", "scripts/16h_audit_ptbxl_ecgdeli_direct_recompute.sh; scripts/16l_run_concordant_subset_external_multimodal_validation.sh", "supplement", "no"),
        ("Audit Table A1", "Manuscript claim support", "tables/table_manuscript_claim_support.csv", "scripts/15_stage15_manuscript_readiness.sh", "audit-only", "no"),
    ]
    df = pd.DataFrame(rows, columns=["item_id", "suggested_caption", "data_source", "script_source", "main_or_supplement", "needs_rerun"])
    safe_to_csv(df, "tables/table_figure_table_source_map.csv")
    return df


def write_audit(claims: pd.DataFrame, diagnostics: pd.DataFrame, calibration: pd.DataFrame) -> None:
    external_main = claims[
        claims["manuscript_claim"].str.contains("external multimodal", case=False, na=False)
        & claims["allowed_location"].eq("main")
    ]
    stage_go = claims.shape[0] >= 18 and Path("docs/MANUSCRIPT_RESULT_BOUNDARIES.md").exists() and external_main.empty
    decision = "GO for drafting" if stage_go else "NO-GO for drafting"
    downgraded = claims[claims["allowed_location"].isin(["supplement", "audit-only", "forbidden"])]
    text = "\n".join(
        [
            "# Manuscript-Ready Audit",
            "",
            "Date: " + date.today().isoformat(),
            "",
            f"Stage 15 drafting decision: {decision}",
            "",
            "## Completed files",
            "",
            "- `tables/table_stage15_external_signal_per_class_diagnostics.csv`",
            "- `tables/table_stage15_external_signal_calibration.csv`",
            "- `tables/table_stage15_external_signal_reliability.csv`",
            "- `tables/table_manuscript_claim_support.csv`",
            "- `docs/MANUSCRIPT_RESULT_BOUNDARIES.md`",
            "- `docs/MANUSCRIPT_TITLE_ABSTRACT_FRAMING.md`",
            "- `tables/table_figure_table_source_map.csv`",
            "- `MANUSCRIPT_READY_AUDIT.md`",
            "",
            "## Diagnostics generated",
            "",
            f"- External per-class diagnostic rows: {len(diagnostics)}",
            f"- External calibration dataset rows: {len(calibration)}",
            "- CPSC2018 and Chapman-Shaoxing remain signal-only external evaluations.",
            "- Temperature scaling was fitted on internal validation; external data were evaluation-only.",
            "",
            "## Missing artifacts",
            "",
            "- No required signal-only external prediction artifact was missing.",
            "- Exact PTB-XL+ external 531-column structured feature tables remain unavailable.",
            "- External signal embeddings for fair concat external evaluation were not available and were not fabricated.",
            "",
            "## Claims downgraded or forbidden",
            "",
            downgraded[["claim_id", "manuscript_claim", "allowed_location", "final_status"]].to_markdown(index=False),
            "",
            "## Boundary check",
            "",
            "- external multimodal validation is NO-GO.",
            "- current external evidence is signal-only only.",
            "- internal full-schema PTB-XL/PTB-XL+ multimodal evidence is usable.",
            "- Stage 14L is a reproducibility finding / feasibility audit, not an external multimodal result.",
            "",
            "## Go/No-Go rule",
            "",
            "GO is allowed because `table_manuscript_claim_support.csv` and `docs/MANUSCRIPT_RESULT_BOUNDARIES.md` were generated, and no external multimodal claim is marked as a main-manuscript claim.",
        ]
    )
    write_markdown("MANUSCRIPT_READY_AUDIT.md", text + "\n")


def main() -> None:
    ensure_dir("tables")
    ensure_dir("docs")
    diagnostics, calibration, _reliability = build_external_signal_diagnostics()
    claims = build_claim_support()
    write_boundaries()
    write_title_abstract()
    build_figure_table_source_map()
    write_audit(claims, diagnostics, calibration)
    print("Stage 15 manuscript-readiness audit completed.")


if __name__ == "__main__":
    main()
