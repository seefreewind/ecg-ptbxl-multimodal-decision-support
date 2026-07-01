# Stage 9 Calibration and Reliability Summary

## Stage status

Stage 9 completed for raw calibration and reliability analysis on the existing frozen validation/test prediction files.

Update after Stage 9B: logits have now been exported for all five main neural-network models, and validation-only temperature scaling has been fitted successfully. See `results/stage9b_logits_temperature_summary.md` for the current calibration results.

Original Stage 9 limitation: temperature scaling was not fitted because none of the five main model prediction files contained per-class logits.

Stage 9B resolved this limitation by exporting logits from frozen checkpoints and rerunning the calibration pipeline. The old skipped-temperature interpretation is superseded by the Stage 9B summary.

## Models included

Main calibration set:

- `strong_signal_only`
- `signal_embedding_mlp`
- `structured_mlp`
- `fair_concat_mlp`
- `gated_fusion_mlp`

Supplementary only:

- `late_probability_concat`

The supplementary late-probability concat model remains excluded from the main fair-fusion comparison.

## Prediction manifest

Output:

- `results/calibration/prediction_manifest.csv`

Manifest result:

- rows: 6
- probability columns available: yes for all listed models
- logit columns available: no for all listed models
- main calibration models: 5

## Raw calibration results on frozen test split

| model | macro Brier | macro ECE | macro MCE |
|---|---:|---:|---:|
| strong_signal_only | 0.091046 | 0.037004 | 0.190803 |
| signal_embedding_mlp | 0.089572 | 0.038058 | 0.157668 |
| structured_mlp | 0.094392 | 0.026258 | 0.147482 |
| fair_concat_mlp | 0.088112 | 0.042286 | 0.180797 |
| gated_fusion_mlp | 0.085785 | 0.035572 | 0.182847 |
| late_probability_concat | 0.120477 | 0.110748 | 0.336086 |

Interpretation:

- The gated fusion model has the lowest raw macro Brier among the main models.
- The structured MLP has the lowest raw macro ECE among the main models.
- The non-fair late-probability concat model remains poorly calibrated and should stay supplementary.
- These calibration results do not rescue a "gated fusion is materially superior" claim because the discriminative difference from fair concat remains very small and statistically unclear.

## Temperature scaling status

Output JSON files:

- `results/calibration/temperature_params_signal_strong.json`
- `results/calibration/temperature_params_signal_embedding_mlp.json`
- `results/calibration/temperature_params_structured_mlp.json`
- `results/calibration/temperature_params_fair_concat.json`
- `results/calibration/temperature_params_gated_fusion.json`

Status:

- fitted: 0
- skipped: 5
- reason: validation/test prediction files contain probabilities but not logits

The following tables were still generated for a stable pipeline, but they should be interpreted as raw-probability carry-through rather than true temperature-scaled results:

- `results/calibration/calibration_metrics_temperature_scaled.csv`
- `tables/table_calibration_temperature_scaled.csv`
- `tables/table_calibration_delta.csv`

## Reliability outputs

Source data:

- `results/calibration/reliability_curve_source_data.csv`
- `results/calibration/confidence_histogram_source_data.csv`

Figures:

- `figures/calibration/reliability_raw_<model>.png`
- `figures/calibration/reliability_temperature_scaled_<model>.png`
- `figures/calibration/confidence_histogram_<model>.png`
- `figures/calibration/reliability_comparison_main_models.png`

Because temperature scaling was skipped, temperature-scaled figures currently duplicate raw-probability behavior.

## Bootstrap calibration confidence intervals

Output:

- `results/calibration/calibration_bootstrap_ci.csv`
- `tables/table_calibration_bootstrap_ci.csv`

Frozen test results:

| model | metric | estimate | 95% CI lower | 95% CI upper |
|---|---|---:|---:|---:|
| strong_signal_only | macro_brier | 0.091046 | 0.086721 | 0.096056 |
| strong_signal_only | macro_ece | 0.037004 | 0.034411 | 0.045350 |
| structured_mlp | macro_brier | 0.094392 | 0.089933 | 0.098877 |
| structured_mlp | macro_ece | 0.026258 | 0.025032 | 0.035480 |
| fair_concat_mlp | macro_brier | 0.088112 | 0.083189 | 0.092890 |
| fair_concat_mlp | macro_ece | 0.042286 | 0.038546 | 0.050247 |
| gated_fusion_mlp | macro_brier | 0.085785 | 0.081043 | 0.090300 |
| gated_fusion_mlp | macro_ece | 0.035572 | 0.032753 | 0.043604 |

## Gated fusion vs fair concat

Output:

- `tables/table_gated_vs_fair_concat_calibration.csv`
- `results/calibration/gated_vs_fair_concat_paired_bootstrap.csv`
- `tables/table_gated_vs_fair_concat_paired_bootstrap.csv`

Discrimination on frozen test:

| metric | fair concat | gated fusion | delta gated - fair concat |
|---|---:|---:|---:|
| AUROC | 0.919251 | 0.919570 | 0.000319 |
| AP | 0.795289 | 0.797779 | 0.002489 |
| F1 | 0.720762 | 0.725463 | 0.004702 |

Paired bootstrap, gated minus fair concat:

| metric | delta | 95% CI lower | 95% CI upper | CI contains 0 |
|---|---:|---:|---:|---|
| AUROC | 0.000319 | -0.001528 | 0.002108 | yes |
| AP | 0.002489 | -0.001366 | 0.007008 | yes |
| F1 | 0.004702 | -0.004387 | 0.014180 | yes |

Conclusion:

The paired bootstrap supports the revised interpretation that gated fusion has no statistically clear advantage over fair MLP-concat on the frozen test set. The paper narrative should therefore not claim that the gating mechanism is the core performance driver.

## Revised paper narrative

The supported story is:

> Strict fair multimodal evaluation shows that ECG signal embeddings and PTB-XL+ structured features are complementary. Simple fair concat already captures the main multimodal gain over either single modality, while gated fusion does not provide a statistically clear additional advantage. The remaining decision-support novelty should come from calibration, uncertainty, interpretability, decision-curve analysis, and external validation.

Supporting narrative file:

- `docs/REVISED_MULTIMODAL_STORY.md`

## Generated files

Core results:

- `results/calibration/prediction_manifest.csv`
- `results/calibration/calibration_metrics_raw.csv`
- `results/calibration/calibration_metrics_temperature_scaled.csv`
- `results/calibration/calibration_metrics_bins_sensitivity.csv`
- `results/calibration/calibration_bootstrap_ci.csv`
- `results/calibration/gated_vs_fair_concat_paired_bootstrap.csv`
- `results/stage9_calibration_summary.md`

Tables:

- `tables/table_calibration_raw.csv`
- `tables/table_calibration_temperature_scaled.csv`
- `tables/table_calibration_delta.csv`
- `tables/table_calibration_bootstrap_ci.csv`
- `tables/table_gated_vs_fair_concat_calibration.csv`
- `tables/table_gated_vs_fair_concat_paired_bootstrap.csv`

Figures:

- `figures/calibration/reliability_comparison_main_models.png`
- per-model reliability and confidence histogram PNG files in `figures/calibration/`

Code and scripts:

- `src/evaluation/calibration.py`
- `src/evaluation/reliability.py`
- `src/evaluation/collect_model_predictions.py`
- `src/evaluation/temperature_scaling.py`
- `src/evaluation/evaluate_calibration.py`
- `src/evaluation/plot_reliability.py`
- `src/evaluation/bootstrap_calibration.py`
- `scripts/09_collect_prediction_manifest.sh`
- `scripts/09a_fit_temperature_scaling.sh`
- `scripts/09b_evaluate_calibration.sh`
- `scripts/09c_plot_reliability.sh`
- `scripts/09d_bootstrap_calibration_metrics.sh`

Tests:

- `tests/test_calibration_metrics.py`
- `tests/test_temperature_scaling.py`
- `tests/test_reliability_outputs.py`
- `tests/test_prediction_manifest.py`

## Verification

Commands run:

```bash
bash scripts/09_collect_prediction_manifest.sh
bash scripts/09a_fit_temperature_scaling.sh
bash scripts/09b_evaluate_calibration.sh
bash scripts/09c_plot_reliability.sh
bash scripts/09d_bootstrap_calibration_metrics.sh
python3 -m pytest tests/ -q
```

Test result:

```text
44 passed, 110 warnings
```

Warnings are the expected small dry-run/single-class metric warnings already present in earlier tests.

## Blocking issue

Strict temperature scaling cannot be fitted until model prediction exports include per-class logits for validation and test splits.

## Next step

Two valid options:

1. Rerun/export the five main model predictions with logits, then rerun `scripts/09a_fit_temperature_scaling.sh` through `scripts/09d_bootstrap_calibration_metrics.sh`.
2. If raw calibration is considered sufficient for now, proceed to uncertainty analysis next.

Do not tune gated fusion further on the frozen test set to force a larger advantage over fair concat.
