# Stage 5 Simple Concat Fusion Baseline Summary

Generated date: 2026-06-28

## 1. Stage Status

Stage 5 completed.

This stage implemented and ran a simple concat fusion baseline. The fusion baseline uses frozen signal-model probability features together with leakage-safe PTB-XL+ structured ECG features.

No gated fusion, XAI, uncertainty analysis, DCA, external validation, or manuscript writing was performed in this stage.

## 2. Inputs

Signal source:

```text
results/internal/signal_resnet.pt
```

Structured source:

```text
data/processed/ptbxl_structured_features.csv
data/processed/ptbxl_multimodal_index.csv
data/processed/structured_feature_names.txt
```

Fusion features:

- structured PTB-XL+ ECG features: 531
- frozen signal model probability features: 5
- total fusion features: 536

Rows:

| split | rows |
|---|---:|
| train | 17418 |
| validation | 2183 |
| test | 2198 |

## 3. Implemented Files

```text
src/training/train_concat_fusion.py
configs/model_concat_fusion.yaml
scripts/06_train_concat_fusion_baseline.sh
tests/test_concat_fusion_baseline.py
```

## 4. Run Command

```bash
bash scripts/06_train_concat_fusion_baseline.sh
```

Generated signal probability features:

```text
results/internal/concat_fusion_signal_train_features.csv
results/internal/concat_fusion_signal_val_features.csv
results/internal/concat_fusion_signal_test_features.csv
```

Generated fusion outputs:

```text
results/internal/concat_fusion_metrics.csv
tables/table_concat_fusion_results.csv
results/internal/concat_fusion_val_predictions.csv
results/internal/concat_fusion_test_predictions.csv
results/internal/concat_fusion_run_summary.json
results/internal/concat_fusion_logistic.pkl
```

## 5. Results

Macro results:

| split | AUROC | average precision | F1 | positive count |
|---|---:|---:|---:|---:|
| validation | 0.899237 | 0.734176 | 0.699751 | 2786 |
| test | 0.892704 | 0.733992 | 0.683037 | 2792 |

For comparison from prior stages:

| model | split | AUROC | average precision | F1 |
|---|---|---:|---:|---:|
| signal-only | test | 0.861169 | 0.686688 | 0.587899 |
| structured-only | test | 0.874455 | 0.690973 | 0.655017 |
| simple concat fusion | test | 0.892704 | 0.733992 | 0.683037 |

These are internal PTB-XL validation/test engineering results only. They are not external validation results and should not be described as clinical validation.

## 6. Verification

Full test command:

```bash
python3 -m pytest tests/ -q
```

Result:

```text
23 passed
```

Warnings in the full test suite come from intentionally tiny dry-run metric tests with single-class labels. They do not affect the real concat fusion outputs.

## 7. Current Readiness Decision

Ready for the next staged modeling step.

Completed:

- signal-only baseline
- PTB-XL+ leakage-safe validation
- PTB-XL/PTB-XL+ alignment
- structured-only baseline
- simple concat fusion baseline

Not completed:

- gated fusion
- ablation
- calibration
- uncertainty
- XAI
- external validation
- manuscript results writing

## 8. Next Step

Proceed to gated fusion baseline only after preserving the simple concat baseline as the reference fusion comparator.

Recommended next implementation:

```text
src/models/gated_fusion.py
src/training/train_gated_fusion.py
configs/model_gated_fusion.yaml
scripts/07_train_gated_fusion_baseline.sh
tests/test_gated_fusion_baseline.py
```
