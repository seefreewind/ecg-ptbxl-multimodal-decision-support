# BMC MIDM Scientific Hardening Log

Date: 2026-06-30

## Purpose

This step strengthened the statistical support for the BMC MIDM-oriented ECG/PTB-XL manuscript while preserving the locked evidence boundary:

- Internal PTB-XL/PTB-XL+ multimodal evaluation is allowed.
- Signal-only external validation on CPSC2018 and Chapman-Shaoxing is allowed.
- Stage 14L is a structured-feature reproducibility and feasibility audit.
- External multimodal validation is NO-GO.
- No clinical readiness, clinical validation, deployment, or additional benefit from gated fusion is claimed.

## Prediction Files Used

Paired bootstrap testing used frozen internal test prediction files:

- Fair MLP-concat: `results/internal/fair_concat/fair_concat_test_predictions.csv`
- Signal-embedding MLP: `results/internal/ablation_signal_embedding/signal_embedding_mlp_test_predictions.csv`
- Strong signal-only: `results/internal/signal_strong/signal_strong_test_predictions.csv`

All three files were present. Records were paired by `ecg_id`. The paired internal test set contained 2,198 records.

## Bootstrap Settings

- Resampling unit: internal test-set ECG record.
- Bootstrap type: paired record-level bootstrap.
- Number of bootstrap replicates: 2,000.
- Random seed: 2026.
- Metrics:
  - macro AUROC
  - macro average precision
  - macro F1
- F1 threshold: per-class probability threshold of 0.5, matching the existing gated-versus-fair-concat paired bootstrap implementation.
- Confidence interval: percentile 95% interval using the 2.5th and 97.5th percentiles.

## Fair Concat Versus Signal-Embedding MLP

| Metric | Fair concat | Signal-embedding MLP | Delta fair-signal | 95% CI | CI contains 0 |
|:---|---:|---:|---:|:---|:---|
| AUROC | 0.9193 | 0.9094 | +0.0098 | +0.0067 to +0.0131 | no |
| AP | 0.7953 | 0.7724 | +0.0229 | +0.0157 to +0.0302 | no |
| F1 | 0.7208 | 0.7002 | +0.0205 | +0.0088 to +0.0324 | no |

Interpretation:

Fair concat showed a statistically supported internal improvement over the signal-embedding comparator for AUROC, AP, and F1. This supports the internal PTB-XL/PTB-XL+ multimodal complementarity claim.

## Fair Concat Versus Strong Signal-Only

| Metric | Fair concat | Strong signal-only | Delta fair-signal | 95% CI | CI contains 0 |
|:---|---:|---:|---:|:---|:---|
| AUROC | 0.9193 | 0.9098 | +0.0094 | +0.0062 to +0.0127 | no |
| AP | 0.7953 | 0.7721 | +0.0232 | +0.0151 to +0.0308 | no |
| F1 | 0.7208 | 0.6998 | +0.0209 | +0.0098 to +0.0319 | no |

Interpretation:

Fair concat also showed a statistically supported internal improvement over the strong signal-only model for AUROC, AP, and F1. This strengthens the manuscript's main positive internal claim.

## Main Claim Status

The main positive claim was **strengthened**, not softened.

Allowed wording:

- Fair concat showed statistically supported internal improvement over the strongest unimodal comparators.
- The finding supports internal PTB-XL/PTB-XL+ multimodal complementarity under frozen splits.

Required boundary:

- This is internal PTB-XL/PTB-XL+ evidence only.
- It must not be transferred to external datasets.
- It must not be described as external multimodal validation.

## External Per-Class Diagnostic Tables

Generated outputs:

- `manuscript/tables/supp_table_external_per_class_diagnostics.csv`
- `manuscript/tables/supp_table_external_per_class_diagnostics.md`

Per-class diagnostics:

| Dataset | Label | Positive cases | Prevalence | AUROC | AP | F1 | Threshold source |
|:---|:---|---:|---:|---:|---:|---:|:---|
| CPSC2018 | NORM | 891 | 0.0896 | 0.9119 | 0.5256 | 0.4344 | PTB-XL validation |
| CPSC2018 | CD | 2,885 | 0.2901 | 0.9022 | 0.7763 | 0.7464 | PTB-XL validation |
| Chapman-Shaoxing | MI | 123 | 0.0027 | 0.9349 | 0.0796 | 0.0277 | PTB-XL validation |
| Chapman-Shaoxing | CD | 3,058 | 0.0677 | 0.8388 | 0.2624 | 0.3319 | PTB-XL validation |
| Chapman-Shaoxing | HYP | 751 | 0.0166 | 0.8488 | 0.1760 | 0.1353 | PTB-XL validation |

Manuscript update:

- Results now reference these diagnostics when explaining low Chapman-Shaoxing AP/F1.
- Discussion now links Chapman-Shaoxing low AP/F1 to prevalence, label mapping, and PTB-XL validation-threshold transfer with data support.

## Wording Changes

The word `infeasible` was removed from the BMC MIDM revision package.

Preferred wording now used:

- "insufficient to support external multimodal validation"
- "not validated with adequate coverage and fidelity"
- "not achieved with sufficient external structured-feature coverage"
- "not supported by the current reproducibility audit"

The manuscript avoids implying that external structured-feature reconstruction is impossible in principle. It states only that the current reproducibility-validated attempt did not provide sufficient fidelity and coverage to justify external multimodal validation.

## Claim Audit

Audited phrases:

- external multimodal validation
- clinically ready
- clinically validated
- deployable
- real-world deployment
- clinical utility proven
- gated fusion superiority
- infeasible
- superior performance
- robust clinical utility

Outcome:

- External multimodal validation appears only as a NO-GO boundary or a non-performed analysis.
- Clinical readiness/deployment language appears only in forbidden-boundary or negative contexts.
- `infeasible` was removed.
- No "clinical utility proven", "superior performance", or "robust clinical utility" claims were present.
- The previous wording around gated fusion was revised to "no additional benefit from gating beyond fair concat."

## Manuscript Package Updated

Updated file:

- `manuscript/BMC_MIDM_REVISION_STEP.md`

New result files:

- `manuscript/tables/table_internal_multimodal_gain_bootstrap.csv`
- `manuscript/tables/table_internal_multimodal_gain_bootstrap.md`
- `manuscript/tables/supp_table_external_per_class_diagnostics.csv`
- `manuscript/tables/supp_table_external_per_class_diagnostics.md`

## Remaining Unresolved Items

- Author-specific declarations remain placeholders.
- Dataset URLs and code repository URL remain placeholders.
- Reference verification and BMC final formatting remain incomplete.
- Figure rendering and final placement remain pending.
- External multimodal validation remains NO-GO until structured-feature reconstruction is validated externally with adequate fidelity and coverage.

## Final Quality Gate

Status: **GO for BMC MIDM scientific manuscript refinement.**

Reason:

- The main internal multimodal gain now has paired bootstrap support.
- External signal-only limitations are supported by per-class diagnostics.
- Stage 14L remains a reproducibility and feasibility audit.
- The package remains a public-data decision-support evaluation study.

Status: **NO-GO for final submission package.**

Reason:

- Administrative declarations and URLs are incomplete.
- References and figures still require final verification and formatting.
