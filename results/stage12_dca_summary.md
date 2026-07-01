# Stage 12 Decision Curve Analysis Summary

Date: 2026-06-29

## Status

Stage 12 DCA is complete for the internal frozen PTB-XL test set.

This stage evaluated decision-curve net benefit using temperature-scaled predictions only. It did not retrain models, tune on the test set, run external validation, or make clinical-readiness claims.

## Models

Main comparison models:

- `strong_signal_only`
- `structured_mlp`
- `fair_concat_mlp`
- `gated_fusion_mlp`

Supplementary model:

- `signal_embedding_mlp`

Late probability concat remains supplementary and was not used as a main DCA model.

## Methods

- DCA was computed separately for `NORM`, `MI`, `STTC`, `CD`, and `HYP`.
- Macro DCA was computed as the mean label-wise net benefit.
- The full threshold-probability grid was `0.01` to `0.50`.
- The main reporting range was `0.05` to `0.40`.
- Retained-subset DCA used Stage 10 validation-selected uncertainty cutoffs at 80% coverage.
- Bootstrap CIs used 1000 resamples with seed `2026`.

## Main Internal DCA Results

Mean macro net benefit over threshold probabilities 0.05-0.40:

| model | mean macro net benefit | max macro net benefit | threshold at max |
|---|---:|---:|---:|
| `gated_fusion_mlp` | 0.189506 | 0.229864 | 0.05 |
| `fair_concat_mlp` | 0.188100 | 0.229970 | 0.05 |
| `strong_signal_only` | 0.184445 | 0.228916 | 0.05 |
| `structured_mlp` | 0.181541 | 0.228677 | 0.05 |

Interpretation:

The two multimodal models showed slightly higher internal macro net benefit than either single-modality baseline across the main threshold range. The gated model had the highest mean macro net benefit on the full test set, but the margin over fair concat was small. This should be interpreted as similar decision-curve behavior rather than evidence that gated fusion has a clinically meaningful advantage over fair concat.

## Retained 80% High-Confidence Subset

Mean macro net benefit over threshold probabilities 0.05-0.40:

| model | mean macro net benefit |
|---|---:|
| `fair_concat_mlp` | 0.190911 |
| `strong_signal_only` | 0.190380 |
| `gated_fusion_mlp` | 0.190046 |
| `structured_mlp` | 0.182103 |

Interpretation:

The retained-subset analysis remains exploratory. It used validation-selected uncertainty cutoffs and frozen-test evaluation. Fair concat was slightly higher than gated fusion in this subset, reinforcing the conservative conclusion that gated fusion does not show a stable DCA advantage over fair concat.

## Bootstrap CI Outputs

Bootstrap CIs were generated for macro net benefit, macro net benefit versus treat-all, and macro net benefit versus treat-none at thresholds 0.10, 0.20, 0.30, and 0.40.

Macro net benefit examples:

| model | threshold | estimate | 95% CI |
|---|---:|---:|---:|
| `strong_signal_only` | 0.10 | 0.213133 | 0.207855-0.218553 |
| `fair_concat_mlp` | 0.10 | 0.214609 | 0.209402-0.219948 |
| `gated_fusion_mlp` | 0.10 | 0.214781 | 0.209380-0.220223 |
| `strong_signal_only` | 0.20 | 0.187716 | 0.181663-0.193426 |
| `fair_concat_mlp` | 0.20 | 0.190810 | 0.185144-0.196338 |
| `gated_fusion_mlp` | 0.20 | 0.192175 | 0.186555-0.197683 |
| `strong_signal_only` | 0.30 | 0.167308 | 0.161379-0.173782 |
| `fair_concat_mlp` | 0.30 | 0.172403 | 0.166410-0.179137 |
| `gated_fusion_mlp` | 0.30 | 0.173937 | 0.167919-0.180711 |
| `strong_signal_only` | 0.40 | 0.147710 | 0.141065-0.154807 |
| `fair_concat_mlp` | 0.40 | 0.153594 | 0.146921-0.160998 |
| `gated_fusion_mlp` | 0.40 | 0.154625 | 0.147619-0.161331 |

## Generated Files

Code:

- `src/evaluation/dca.py`
- `src/evaluation/evaluate_dca.py`
- `src/evaluation/plot_dca.py`
- `src/evaluation/bootstrap_dca.py`

Scripts:

- `scripts/13_evaluate_dca.sh`
- `scripts/13b_plot_dca.sh`
- `scripts/13c_bootstrap_dca.sh`

Results and tables:

- `results/dca/dca_threshold_grid.csv`
- `results/dca/dca_results_by_label.csv`
- `results/dca/dca_results_macro.csv`
- `results/dca/dca_results_retained_80_coverage.csv`
- `results/dca/dca_bootstrap_ci.csv`
- `tables/table_dca_by_label.csv`
- `tables/table_dca_summary.csv`
- `tables/table_dca_retained_80_coverage.csv`
- `tables/table_dca_bootstrap_ci.csv`

Figures:

- `figures/dca/dca_macro_main_models.png`
- `figures/dca/dca_macro_main_models.svg`
- `figures/dca/dca_by_label_main_models.png`
- `figures/dca/dca_by_label_main_models.svg`
- `figures/dca/dca_fair_concat_vs_gated.png`
- `figures/dca/dca_fair_concat_vs_gated.svg`
- `figures/dca/dca_threshold_range_sensitivity.png`
- `figures/dca/dca_threshold_range_sensitivity.svg`
- `figures/dca/dca_retained_80_coverage.png`
- `figures/dca/dca_retained_80_coverage.svg`
- `figures/main/fig8_dca.png`
- `figures/main/fig8_dca.svg`

Figure 8 source data:

- `figures/source_data/fig8_dca_macro.csv`
- `figures/source_data/fig8_dca_by_label.csv`
- `figures/source_data/fig8_dca_retained_80_coverage.csv`
- `figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv`

Tests:

- `tests/test_dca.py`
- `tests/test_dca_outputs.py`
- `tests/test_dca_figure_source_data.py`
- `tests/test_dca_no_test_tuning.py`

## Verification

Commands run:

```bash
bash scripts/13_evaluate_dca.sh
bash scripts/13b_plot_dca.sh
bash scripts/13c_bootstrap_dca.sh
bash scripts/12c_check_figure_source_data.sh
```

Observed status:

- DCA tables generated.
- DCA figures generated.
- Bootstrap CI table generated with 36 rows.
- Figure source-data QC completed with `failed=0`.

## Current Interpretation Boundary

The defensible claim after Stage 12 is:

```text
Internal decision-curve analysis supports the practical utility of multimodal prediction relative to single-modality baselines, but gated fusion does not demonstrate a stable or clinically meaningful decision-curve advantage over fair concat.
```

The project should continue to avoid:

- claiming gated fusion superiority;
- claiming clinical readiness;
- using external validation language before external validation is actually run;
- tuning additional modeling decisions on the frozen test set.

## Next Step

Proceed to external validation only after confirming the external cohort mapping and label compatibility. External validation should be reported conservatively and should not be used to revise frozen internal-test conclusions.
