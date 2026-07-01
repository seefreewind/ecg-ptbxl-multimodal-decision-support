# Stage 10 Uncertainty and Risk-Coverage Triage Summary

## 1. Stage Status

- status: completed
- new model training: no
- model architecture changes: no
- XAI / DCA / external validation: not performed
- validation-only cutoff selection: confirmed
- frozen test role: final evaluation only

This stage evaluates whether uncertainty can identify high-confidence ECGs for higher-confidence decision support while routing low-confidence ECGs to clinician review. It does not support autonomous diagnosis or clinical-readiness claims.

## 2. Models Included

Main models:

- `strong_signal_only`
- `fair_concat_mlp`
- `gated_fusion_mlp`

Supplementary models:

- `signal_embedding_mlp`
- `structured_mlp`

The late-probability concat model remains excluded from the main analysis.

## 3. Uncertainty Scores

Implemented:

- `entropy_macro`: mean binary entropy across the five labels
- `entropy_max`: maximum binary entropy across the five labels
- `margin_uncertainty`: negative minimum distance to the validation-tuned class thresholds

Direction:

- larger `entropy_macro` = more uncertain
- larger `entropy_max` = more uncertain
- larger `margin_uncertainty` = more uncertain because it is defined as `-min(abs(probability - threshold))`

Not implemented in this stage:

- seed-ensemble uncertainty: skipped; can be added later from repeated-seed predictions
- MC-Dropout: skipped because dropout-enabled inference was not yet validated for frozen checkpoints

## 4. Primary Score Selection

Primary probability mode:

- `temperature_scaled`

Primary uncertainty score:

- `entropy_macro`

Reason:

- It showed stable monotonic triage behavior across the main models.
- At 80% coverage, retained-set performance improved versus 100% coverage for all three main models.
- It was more stable than `margin_uncertainty` and generally stronger than `entropy_max`.

## 5. Validation-Only Cutoff Selection

Coverage levels:

- 100%
- 90%
- 80%
- 70%
- 60%
- 50%

Cutoff output:

- `results/uncertainty/triage_cutoffs_validation.csv`

Rules:

- all cutoffs were selected on validation only
- frozen test did not participate in cutoff selection
- 100% coverage uses an infinite uncertainty cutoff so all frozen-test samples are retained

## 6. Risk-Coverage Results

Primary test results using temperature-scaled probabilities and `entropy_macro`:

| model | coverage | retained AUROC | retained F1 | referral fraction | retained Brier | retained ECE |
|---|---:|---:|---:|---:|---:|---:|
| strong_signal_only | 100% | 0.909815 | 0.710207 | 0.000000 | 0.090266 | 0.031984 |
| strong_signal_only | 90% | 0.917173 | 0.725650 | 0.098271 | 0.082285 | 0.029150 |
| strong_signal_only | 80% | 0.923722 | 0.741959 | 0.201092 | 0.073534 | 0.025553 |
| strong_signal_only | 70% | 0.928696 | 0.753547 | 0.310282 | 0.064647 | 0.020286 |
| fair_concat_mlp | 100% | 0.919251 | 0.724041 | 0.000000 | 0.086356 | 0.028284 |
| fair_concat_mlp | 90% | 0.925670 | 0.744449 | 0.096451 | 0.078108 | 0.026190 |
| fair_concat_mlp | 80% | 0.931531 | 0.757469 | 0.201092 | 0.069775 | 0.022498 |
| fair_concat_mlp | 70% | 0.936068 | 0.763334 | 0.296633 | 0.063375 | 0.021340 |
| gated_fusion_mlp | 100% | 0.919570 | 0.731378 | 0.000000 | 0.084421 | 0.019276 |
| gated_fusion_mlp | 90% | 0.925794 | 0.750449 | 0.099181 | 0.075783 | 0.016541 |
| gated_fusion_mlp | 80% | 0.930250 | 0.759668 | 0.200637 | 0.068678 | 0.016064 |
| gated_fusion_mlp | 70% | 0.935766 | 0.774961 | 0.303913 | 0.060010 | 0.016025 |

## 7. Best Operating Points

At 90% coverage:

- best retained F1: `gated_fusion_mlp`, 0.750449
- best retained AUROC: `gated_fusion_mlp`, 0.925794
- referral fraction: about 9.9%

At 80% coverage:

- best retained F1: `gated_fusion_mlp`, 0.759668
- best retained AUROC: `fair_concat_mlp`, 0.931531
- referral fraction: about 20%

At 70% coverage:

- best retained F1: `gated_fusion_mlp`, 0.774961
- best retained AUROC: `fair_concat_mlp`, 0.936068
- referral fraction: about 30%

Interpretation:

- Uncertainty triage improves retained-set performance as coverage decreases.
- The multimodal models outperform strong signal-only at the same coverage levels.
- Gated fusion has slightly better retained F1 and calibration in this triage analysis, while fair concat has slightly better retained AUROC at 80% and 70% coverage. This should be described cautiously and not as definitive gated superiority.

## 8. Referred Subset Characteristics

At 80% coverage with temperature-scaled `entropy_macro`:

| model | referred n | referral fraction | mean predicted labels | mean entropy | error rate | MI prevalence | STTC prevalence | CD prevalence | HYP prevalence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| strong_signal_only | 442 | 0.201092 | 1.877828 | 0.471562 | 0.748869 | 0.402715 | 0.357466 | 0.253394 | 0.190045 |
| fair_concat_mlp | 442 | 0.201092 | 1.993213 | 0.467878 | 0.780543 | 0.407240 | 0.416290 | 0.305430 | 0.205882 |
| gated_fusion_mlp | 441 | 0.200637 | 1.820862 | 0.469852 | 0.734694 | 0.401361 | 0.390023 | 0.317460 | 0.204082 |

The referred subset has high error rates and enriched abnormal-label prevalence, supporting the idea that high-uncertainty ECGs are harder and should be routed to clinician review.

## 9. Bootstrap CI

Output:

- `results/uncertainty/uncertainty_triage_bootstrap_ci.csv`
- `tables/table_uncertainty_triage_bootstrap_ci.csv`

At 80% coverage:

| model | metric | estimate | 95% CI lower | 95% CI upper |
|---|---|---:|---:|---:|
| strong_signal_only | retained AUROC | 0.923722 | 0.915091 | 0.932577 |
| strong_signal_only | retained F1 | 0.741959 | 0.724498 | 0.758881 |
| strong_signal_only | retained Brier | 0.073534 | 0.068698 | 0.078108 |
| strong_signal_only | retained ECE | 0.025553 | 0.025243 | 0.035075 |
| fair_concat_mlp | retained AUROC | 0.931531 | 0.923168 | 0.939663 |
| fair_concat_mlp | retained F1 | 0.757469 | 0.738795 | 0.775218 |
| fair_concat_mlp | retained Brier | 0.069775 | 0.065106 | 0.074249 |
| fair_concat_mlp | retained ECE | 0.022498 | 0.022701 | 0.032440 |
| gated_fusion_mlp | retained AUROC | 0.930250 | 0.921788 | 0.938949 |
| gated_fusion_mlp | retained F1 | 0.759668 | 0.739421 | 0.777471 |
| gated_fusion_mlp | retained Brier | 0.068678 | 0.063952 | 0.073568 |
| gated_fusion_mlp | retained ECE | 0.016064 | 0.017665 | 0.026306 |

## 10. Generated Files

Code:

- `src/evaluation/uncertainty.py`
- `src/evaluation/evaluate_uncertainty_triage.py`
- `src/evaluation/select_triage_cutoffs.py`
- `src/evaluation/risk_coverage.py`
- `src/evaluation/plot_uncertainty_triage.py`
- `src/evaluation/bootstrap_uncertainty_triage.py`

Scripts:

- `scripts/10_evaluate_uncertainty_triage.sh`
- `scripts/10b_plot_uncertainty_triage.sh`
- `scripts/10c_bootstrap_uncertainty_triage.sh`

Results:

- `results/uncertainty/uncertainty_scores_validation.csv`
- `results/uncertainty/uncertainty_scores_test.csv`
- `results/uncertainty/triage_cutoffs_validation.csv`
- `results/uncertainty/risk_coverage_metrics_validation.csv`
- `results/uncertainty/risk_coverage_metrics_test.csv`
- `results/uncertainty/referred_subset_characteristics.csv`
- `results/uncertainty/risk_coverage_curve_source_data.csv`
- `results/uncertainty/uncertainty_triage_bootstrap_ci.csv`
- `results/uncertainty/summary.md`

Tables:

- `tables/table_uncertainty_triage.csv`
- `tables/table_uncertainty_score_comparison.csv`
- `tables/table_referred_subset_characteristics.csv`
- `tables/table_decision_support_triage_summary.csv`
- `tables/table_uncertainty_triage_bootstrap_ci.csv`

Figures:

- `figures/uncertainty/risk_coverage_macro_f1.png`
- `figures/uncertainty/risk_coverage_macro_auroc.png`
- `figures/uncertainty/risk_coverage_referral_tradeoff.png`
- `figures/uncertainty/risk_coverage_main_models.png`

Tests:

- `tests/test_uncertainty_metrics.py`
- `tests/test_risk_coverage.py`
- `tests/test_triage_cutoff_selection.py`
- `tests/test_uncertainty_outputs.py`

## 11. Interpretation for Paper

The triage analysis supports a decision-support workflow in which lower-uncertainty ECGs are retained for higher-confidence model-assisted interpretation and higher-uncertainty ECGs are referred for clinician review.

This is a workflow-level decision-support finding, not a clinical validation claim. External validation is still required before any clinical-readiness statement.

The result also fits the revised paper story: multimodal models offer stronger triage behavior than signal-only, but gated fusion should still not be framed as definitively superior to fair concat.

## 12. Next Recommended Step

Proceed to XAI.

Suggested order:

1. structured-side feature attribution for `structured_mlp`, `fair_concat_mlp`, and `gated_fusion_mlp`
2. signal-side Grad-CAM or saliency for `strong_signal_only`
3. joint explanation examples for high-confidence retained ECGs and low-confidence referred ECGs

Do not start DCA or external validation before XAI is complete.
