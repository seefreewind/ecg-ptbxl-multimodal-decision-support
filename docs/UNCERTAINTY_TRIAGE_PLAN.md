# Uncertainty and Risk-Coverage Triage Plan

## 1. Goal

Convert the classifier into a decision-support workflow by identifying high-confidence cases suitable for automated support and low-confidence cases that should be referred for clinician review.

The goal is not autonomous diagnosis. The intended framing is high-confidence automated decision support plus low-confidence referral to clinicians.

## 2. Models

Primary models:

- `strong_signal_only`
- `fair_concat_mlp`
- `gated_fusion_mlp`

Secondary optional models:

- `signal_embedding_mlp`
- `structured_mlp`

The main uncertainty comparison should prioritize the signal-only baseline, the simple fair multimodal concat model, and the gated fusion model. This keeps the analysis aligned with the revised paper narrative: multimodal complementarity is the main supported performance source, while gated fusion should not be claimed as statistically superior to fair concat.

## 3. Uncertainty Measures

Candidate uncertainty scores:

- predictive entropy from per-class probabilities
- maximum class uncertainty, defined as the maximum binary entropy across labels
- margin uncertainty, using the smallest distance between class probability and the decision threshold
- MC-Dropout variance, if dropout inference is available from frozen checkpoints
- seed-ensemble variance using repeated-seed models

Recommended first pass:

1. deterministic probability-based uncertainty: entropy and margin uncertainty
2. seed-ensemble variance where repeated-seed predictions already exist
3. MC-Dropout only after verifying dropout-enabled inference is stable and does not alter frozen model parameters

## 4. Triage Curves

Report risk-coverage behavior by ranking samples from lowest uncertainty to highest uncertainty using validation-selected thresholds and evaluating on frozen test.

Metrics:

- risk-coverage curve
- retained-set AUROC
- retained-set average precision
- retained-set macro F1
- referral fraction
- retained high-confidence subset performance
- referred low-confidence subset label prevalence

The test set must be used only for final evaluation after all coverage or threshold choices are fixed on validation.

## 5. Coverage Points

Report:

- 100%
- 90%
- 80%
- 70%
- 60%
- 50%

For each coverage point, report the validation-selected uncertainty cutoff and the frozen test retained-set performance.

## 6. Decision-Support Interpretation

Use conservative language:

```text
The uncertainty triage analysis evaluates whether model confidence can identify a subset of ECGs for higher-confidence decision support while routing lower-confidence cases to clinician review.
```

Avoid:

```text
The model can autonomously diagnose cardiac risk.
```

## 7. Safety Constraints

- No test-based threshold tuning.
- Triage thresholds selected on validation and applied to frozen test.
- External validation is still required before clinical claims.
- Do not claim clinical readiness.
- Do not tune gated fusion further on frozen test to force superiority over fair concat.
- Keep signal-only, fair concat, and gated fusion comparisons on the same split and metric definitions.

## 8. Planned Outputs

Suggested files:

- `src/evaluation/uncertainty.py`
- `src/evaluation/evaluate_uncertainty_triage.py`
- `scripts/10_evaluate_uncertainty_triage.sh`
- `results/uncertainty/uncertainty_scores_val.csv`
- `results/uncertainty/uncertainty_scores_test.csv`
- `results/uncertainty/risk_coverage_metrics.csv`
- `tables/table_uncertainty_triage.csv`
- `figures/uncertainty/risk_coverage_curve.png`
- `results/stage10_uncertainty_summary.md`

## 9. Readiness Criteria

Before Stage 10 execution:

- logits are available for the five main models
- prediction manifest marks main models as temperature-scaling eligible
- calibration rerun completed
- uncertainty thresholds will be selected only on validation
- frozen test will remain untouched until final evaluation
