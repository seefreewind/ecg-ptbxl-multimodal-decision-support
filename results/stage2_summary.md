# Stage 2 Summary

## 1. PTB-XL+ Status

- found: missing
- selected feature file: none
- aligned rows: 0
- structured feature columns: 0
- blocking issue: PTB-XL+ structured features are still missing. Multimodal modeling is not allowed yet.

Generated files:

- `docs/PTBXL_PLUS_SETUP.md`
- `src/data/validate_ptbxl_plus.py`
- `scripts/01b_validate_ptbxl_plus.sh`
- `src/data/align_ptbxl_plus.py`
- `scripts/01c_align_ptbxl_plus.sh`
- `results/ptbxl_plus_validation_report.md`
- `results/ptbxl_plus_candidates.csv`

Alignment was not run because validation did not select a valid PTB-XL+ feature file.

## 2. Strong Signal Baseline Status

- strong config created: yes
- full training completed: yes
- device used: MPS
- epochs requested: 50
- epochs completed: 23
- early stopping epoch: 23
- best checkpoint epoch: 15
- best validation macro AUROC: 0.911408
- final frozen test macro AUROC: 0.909815
- default threshold validation macro F1: 0.702952
- default threshold test macro F1: 0.699812
- validation-tuned threshold validation macro F1: 0.722944
- validation-tuned threshold test macro F1: 0.705944

Strong baseline artifacts:

- `configs/model_signal_resnet_strong.yaml`
- `scripts/02b_train_signal_strong_baseline.sh`
- `results/internal/signal_strong/signal_strong_val_predictions.csv`
- `results/internal/signal_strong/signal_strong_test_predictions.csv`
- `results/internal/signal_strong/signal_strong_training_history.csv`
- `results/internal/signal_strong/signal_strong_metrics_val.csv`
- `results/internal/signal_strong/signal_strong_metrics_test.csv`
- `results/internal/signal_strong/signal_strong_run_summary.json`
- `results/internal/signal_strong/signal_strong_best.pt`
- `tables/table_signal_strong_baseline_results.csv`

## 3. Comparison to Dry-Run Baseline

| metric | dry-run validation | strong validation | dry-run test | strong test |
|---|---:|---:|---:|---:|
| macro AUROC | 0.864554 | 0.911408 | 0.861169 | 0.909815 |
| macro average precision | 0.694140 | 0.774016 | 0.686688 | 0.772057 |
| macro F1 at 0.5 | 0.594134 | 0.702952 | 0.587899 | 0.699812 |

Interpretation: the strong signal-only baseline substantially improves over the earlier engineering dry-run across validation and frozen test metrics. This remains a signal-only PTB-XL internal baseline, not a multimodal result.

## 4. Threshold Tuning

Thresholds were selected on validation only and then applied unchanged to test.

| label | validation-tuned threshold |
|---|---:|
| NORM | 0.42 |
| MI | 0.30 |
| STTC | 0.38 |
| CD | 0.51 |
| HYP | 0.34 |

| split | default macro F1 | tuned macro F1 |
|---|---:|---:|
| validation | 0.702952 | 0.722944 |
| test | 0.699812 | 0.705944 |

Generated files:

- `src/training/thresholds.py`
- `results/internal/signal_strong/val_tuned_thresholds.json`
- `tables/table_signal_strong_thresholds.csv`
- `tables/table_signal_strong_threshold_comparison.csv`

## 5. Repeated Seeds and Bootstrap

Repeated seeds completed:

- 2026
- 2027
- 2028

| split | AUROC mean | AUROC SD | average precision mean | average precision SD | F1 mean | F1 SD |
|---|---:|---:|---:|---:|---:|---:|
| validation | 0.907759 | 0.003254 | 0.767181 | 0.006930 | 0.690944 | 0.014108 |
| test | 0.907991 | 0.003199 | 0.768700 | 0.004704 | 0.686995 | 0.015353 |

Bootstrap confidence intervals used 1000 resamples of the strong single-run validation/test prediction files.

| split | metric | estimate | 95% CI lower | 95% CI upper |
|---|---|---:|---:|---:|
| validation | AUROC | 0.911408 | 0.903188 | 0.919375 |
| validation | average precision | 0.774016 | 0.756569 | 0.793261 |
| validation | F1 | 0.702952 | 0.685730 | 0.721518 |
| test | AUROC | 0.909815 | 0.901679 | 0.917527 |
| test | average precision | 0.772057 | 0.755135 | 0.789785 |
| test | F1 | 0.699812 | 0.683909 | 0.716626 |

Generated files:

- `scripts/03b_run_signal_strong_repeated_seeds.sh`
- `results/internal/signal_strong_repeated/signal_strong_repeated_seed_metrics.csv`
- `results/internal/signal_strong_repeated/signal_strong_repeated_seed_summary.csv`
- `tables/table_signal_strong_repeated_seed_summary.csv`
- `scripts/04b_bootstrap_signal_strong_metrics.sh`
- `results/internal/signal_strong_bootstrap_ci.csv`
- `tables/table_signal_strong_bootstrap_ci.csv`

## 6. External Label Mapping Plan

- draft table created: yes
- mapping document created: yes
- datasets covered: CPSC2018 and Chapman-Shaoxing
- target labels: NORM, MI, STTC, CD, HYP

Classes safely mappable now:

- NORM: high-confidence normal labels can be included when source annotations confirm absence of major abnormality.

Classes uncertain pending annotation audit:

- MI
- STTC
- CD
- HYP

Recommended external validation scope: begin with high-confidence NORM and audited disease-specific mappings only. Low-confidence mappings should be used for sensitivity analysis or excluded.

Generated files:

- `docs/EXTERNAL_LABEL_MAPPING_PLAN.md`
- `tables/table_external_label_mapping_draft.csv`

## 7. Current Readiness

Blocked by missing PTB-XL+.

The project is ready for signal-only manuscript baseline only. It is not ready for structured-only baseline or multimodal modeling until PTB-XL+ structured features are placed, validated, and aligned.

## 8. Next Recommended Step

Place valid PTB-XL+ structured feature files under:

```text
data/raw/ptbxl_plus/
```

Then run:

```bash
bash scripts/01b_validate_ptbxl_plus.sh
bash scripts/01c_align_ptbxl_plus.sh
```

If PTB-XL+ aligns successfully with `aligned rows > 10000` and `structured feature columns > 20`, proceed to structured-only baseline. Do not start gated fusion or multimodal conclusions before that step.
