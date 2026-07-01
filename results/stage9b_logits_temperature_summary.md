# Stage 9B Logit Export and Temperature Scaling Summary

## 1. Stage Status

- status: completed
- new training performed: no
- frozen checkpoints used: yes
- validation used for temperature fitting: yes
- frozen test used only for transform/evaluation: yes

Stage 9B fixed the main technical debt from Stage 9: the five main neural-network models now have validation and frozen test prediction CSV files with raw logits and probabilities.

## 2. Logit Export

| model | checkpoint found | validation logits exported | test logits exported | logit columns | probability columns | validation rows | test rows |
|---|---|---|---|---:|---:|---:|---:|
| strong_signal_only | yes | yes | yes | 5 | 5 | 2183 | 2198 |
| signal_embedding_mlp | yes | yes | yes | 5 | 5 | 2183 | 2198 |
| structured_mlp | yes | yes | yes | 5 | 5 | 2183 | 2198 |
| fair_concat_mlp | yes | yes | yes | 5 | 5 | 2183 | 2198 |
| gated_fusion_mlp | yes | yes | yes | 5 | 5 | 2183 | 2198 |

Exported files:

- `results/internal/signal_strong/signal_strong_val_predictions_with_logits.csv`
- `results/internal/signal_strong/signal_strong_test_predictions_with_logits.csv`
- `results/internal/signal_embedding_mlp/signal_embedding_mlp_val_predictions_with_logits.csv`
- `results/internal/signal_embedding_mlp/signal_embedding_mlp_test_predictions_with_logits.csv`
- `results/internal/structured_mlp/structured_mlp_val_predictions_with_logits.csv`
- `results/internal/structured_mlp/structured_mlp_test_predictions_with_logits.csv`
- `results/internal/fair_concat/fair_concat_val_predictions_with_logits.csv`
- `results/internal/fair_concat/fair_concat_test_predictions_with_logits.csv`
- `results/internal/gated_fusion/gated_fusion_val_predictions_with_logits.csv`
- `results/internal/gated_fusion/gated_fusion_test_predictions_with_logits.csv`

Schema:

- `ecg_id`
- `split`
- `y_true_NORM`, `y_true_MI`, `y_true_STTC`, `y_true_CD`, `y_true_HYP`
- `logit_NORM`, `logit_MI`, `logit_STTC`, `logit_CD`, `logit_HYP`
- `prob_NORM`, `prob_MI`, `prob_STTC`, `prob_CD`, `prob_HYP`

The exported probabilities match `sigmoid(logit)` within numerical tolerance.

## 3. Prediction Manifest Update

Output:

- `results/calibration/prediction_manifest.csv`

Manifest status:

- models included: 6
- main models included: 5
- models eligible for temperature scaling: 5
- skipped models: `late_probability_concat`

Skipped supplementary model:

- `late_probability_concat`: probability-only historical non-fair comparator; excluded from main calibration and temperature-scaling claims.

## 4. Temperature Scaling

Output files:

- `results/calibration/temperature_params_signal_strong.json`
- `results/calibration/temperature_params_signal_embedding_mlp.json`
- `results/calibration/temperature_params_structured_mlp.json`
- `results/calibration/temperature_params_fair_concat.json`
- `results/calibration/temperature_params_gated_fusion.json`

Fitted models:

| model | status | temperature type | fitted on split |
|---|---|---|---|
| strong_signal_only | fitted | per_class | validation |
| signal_embedding_mlp | fitted | per_class | validation |
| structured_mlp | fitted | per_class | validation |
| fair_concat_mlp | fitted | per_class | validation |
| gated_fusion_mlp | fitted | per_class | validation |

Validation-only fitting confirmed:

- Temperature parameters were optimized using validation logits and validation labels only.
- Frozen test logits were transformed after fitting.
- Test data were not used to select temperatures or temperature type.

## 5. Raw vs Temperature-Scaled Calibration

Frozen test results:

| model | raw Brier | scaled Brier | delta Brier | raw ECE | scaled ECE | delta ECE |
|---|---:|---:|---:|---:|---:|---:|
| strong_signal_only | 0.091046 | 0.090266 | -0.000780 | 0.037004 | 0.031984 | -0.005020 |
| signal_embedding_mlp | 0.089572 | 0.088321 | -0.001250 | 0.038058 | 0.021689 | -0.016370 |
| structured_mlp | 0.094392 | 0.094208 | -0.000184 | 0.026258 | 0.021226 | -0.005032 |
| fair_concat_mlp | 0.088112 | 0.086356 | -0.001757 | 0.042286 | 0.028284 | -0.014002 |
| gated_fusion_mlp | 0.085785 | 0.084421 | -0.001365 | 0.035572 | 0.019276 | -0.016296 |

Best frozen test macro ECE:

- raw: `structured_mlp`, 0.026258
- temperature-scaled: `gated_fusion_mlp`, 0.019276

Temperature scaling improved frozen test macro ECE for all five main models. The improvement is useful for methodological completeness, but it should not be over-interpreted as clinical readiness.

## 6. Reliability Figures

Generated figures:

- `figures/calibration/reliability_comparison_main_models.png`
- `figures/calibration/reliability_raw_<model>.png`
- `figures/calibration/reliability_temperature_scaled_<model>.png`
- `figures/calibration/confidence_histogram_<model>.png`

Source data:

- `results/calibration/reliability_curve_source_data.csv`
- `results/calibration/confidence_histogram_source_data.csv`

## 7. Bootstrap CI

Output:

- `results/calibration/calibration_bootstrap_ci.csv`
- `tables/table_calibration_bootstrap_ci.csv`

Frozen test bootstrap CI now includes both `raw` and `temperature_scaled` modes for:

- `strong_signal_only`
- `structured_mlp`
- `fair_concat_mlp`
- `gated_fusion_mlp`

Selected temperature-scaled frozen test CI:

| model | metric | estimate | 95% CI lower | 95% CI upper |
|---|---|---:|---:|---:|
| strong_signal_only | macro_brier | 0.090266 | 0.085901 | 0.094731 |
| strong_signal_only | macro_ece | 0.031984 | 0.030215 | 0.040240 |
| structured_mlp | macro_brier | 0.094208 | 0.089991 | 0.098340 |
| structured_mlp | macro_ece | 0.021226 | 0.022074 | 0.031219 |
| fair_concat_mlp | macro_brier | 0.086356 | 0.081846 | 0.090880 |
| fair_concat_mlp | macro_ece | 0.028284 | 0.027969 | 0.037010 |
| gated_fusion_mlp | macro_brier | 0.084421 | 0.079729 | 0.088571 |
| gated_fusion_mlp | macro_ece | 0.019276 | 0.020719 | 0.028818 |

## 8. Interpretation

Temperature scaling was evaluated for methodological completeness and is now properly fit on validation logits rather than skipped.

Calibration was already reasonably strong in several models before scaling. Temperature scaling reduced macro ECE for all five main models on frozen test, especially `signal_embedding_mlp`, `fair_concat_mlp`, and `gated_fusion_mlp`. The Brier improvements were smaller, which is expected when the raw probabilistic predictions are already usable.

The revised paper narrative remains unchanged:

- multimodal fusion improves over single-modality baselines;
- simple fair concat captures most of the multimodal gain;
- gated fusion still does not have statistically clear discriminative superiority over fair concat;
- calibration strengthens the trustworthy decision-support framing but does not establish clinical readiness.

No clinical-readiness claim is made.

## 9. Readiness for Uncertainty

- readiness: Ready for uncertainty analysis
- reason: logits are now available for all five main models and validation-only temperature scaling has completed successfully.

Next planned document:

- `docs/UNCERTAINTY_TRIAGE_PLAN.md`

## Verification

Commands run:

```bash
bash scripts/09e_export_main_model_logits.sh
bash scripts/09_collect_prediction_manifest.sh
bash scripts/09a_fit_temperature_scaling.sh
bash scripts/09b_evaluate_calibration.sh
bash scripts/09c_plot_reliability.sh
bash scripts/09d_bootstrap_calibration_metrics.sh
python3 -m pytest tests/ -q
```

Test result:

```text
51 passed, 110 warnings
```

Warnings are the expected dry-run/single-class metric warnings already present in earlier tests.
