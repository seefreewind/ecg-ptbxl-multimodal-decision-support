# Stage 4 Structured-Only Baseline Summary

Generated date: 2026-06-28

## 1. Stage Status

Stage 4 completed.

This stage completed PTB-XL+ placement, leakage-safe validation, PTB-XL/PTB-XL+ alignment, and a structured-only baseline using PTB-XL+ ECG feature tables.

No concat fusion, gated fusion, XAI, uncertainty analysis, DCA, external validation, or manuscript writing was performed in this stage.

## 2. PTB-XL+ Raw Files

Downloaded and placed under:

```text
data/raw/ptbxl_plus/
```

Key files:

```text
data/raw/ptbxl_plus/features/ecgdeli_features.csv
data/raw/ptbxl_plus/features/12sl_features.csv
data/raw/ptbxl_plus/features/unig_features.csv
data/raw/ptbxl_plus/features/feature_description.csv
data/raw/ptbxl_plus/LICENSE.txt
data/raw/ptbxl_plus/RECORDS
data/raw/ptbxl_plus/SHA256SUMS.txt
```

## 3. Leakage-Safe File Selection

Validation command:

```bash
bash scripts/01b_validate_ptbxl_plus.sh
```

Result:

- selected feature file: `data/raw/ptbxl_plus/features/ecgdeli_features.csv`
- selected file role: `allowed_feature_table`
- blocking issue: none
- excluded metadata file: `features/feature_description.csv`
- labels/statements/mapping files were not used as structured inputs

Generated validation files:

```text
results/ptbxl_plus_file_roles.csv
results/ptbxl_plus_candidates.csv
results/ptbxl_plus_validation_report.md
tables/table_ptbxl_plus_file_audit.csv
```

## 4. PTB-XL+ Alignment

Alignment command:

```bash
bash scripts/01c_align_ptbxl_plus.sh
```

Result:

- PTB-XL rows: 21799
- PTB-XL+ rows: 21799
- aligned rows: 21799
- alignment rate vs PTB-XL: 1.000000
- raw feature columns: 531
- kept feature columns: 531
- dropped feature columns: 1
- readiness: ready

Generated alignment files:

```text
data/processed/ptbxl_structured_features.csv
data/processed/ptbxl_multimodal_index.csv
data/processed/structured_feature_names.txt
tables/table_ptbxl_plus_missingness.csv
tables/table_ptbxl_plus_excluded_columns.csv
tables/table_ptbxl_plus_alignment.csv
results/ptbxl_plus_alignment_report.md
```

## 5. Structured-Only Baseline

Implemented files:

```text
src/training/train_structured.py
configs/model_structured_logistic.yaml
scripts/05_train_structured_baseline.sh
tests/test_structured_baseline.py
```

Training command:

```bash
bash scripts/05_train_structured_baseline.sh
```

Model:

- structured-only logistic baseline
- input: 531 leakage-safe PTB-XL+ ECG features from `ecgdeli_features.csv`
- labels: NORM / MI / STTC / CD / HYP
- split source: `data/processed/ptbxl_multimodal_index.csv`
- preprocessing: train-only median imputation and train-only standardization
- no waveform input used

Rows:

| split | rows |
|---|---:|
| train | 17418 |
| validation | 2183 |
| test | 2198 |

## 6. Structured Baseline Results

Output files:

```text
results/internal/structured_baseline_metrics.csv
tables/table_structured_baseline_results.csv
results/internal/structured_val_predictions.csv
results/internal/structured_test_predictions.csv
results/internal/structured_run_summary.json
results/internal/structured_logistic.pkl
```

Macro results:

| split | AUROC | average precision | F1 | positive count |
|---|---:|---:|---:|---:|
| validation | 0.878361 | 0.680073 | 0.667121 | 2786 |
| test | 0.874455 | 0.690973 | 0.655017 | 2792 |

## 7. Verification

Full test command:

```bash
python3 -m pytest tests/ -q
```

Result:

```text
22 passed
```

Warnings in the full test suite come from intentionally tiny dry-run metric tests with single-class labels. They do not affect the real structured baseline outputs.

## 8. Current Readiness Decision

Ready for the next modeling stage.

The project now has:

- signal-only baseline completed
- PTB-XL+ leakage-safe validation completed
- PTB-XL/PTB-XL+ alignment completed
- structured-only baseline completed

The project is not yet ready for manuscript claims about a completed multimodal framework, gated fusion, explainability, uncertainty, DCA, or external validation.

## 9. Next Step

Proceed to simple concat fusion baseline:

```text
PTB-XL waveform signal embedding + PTB-XL+ structured ECG features -> NORM / MI / STTC / CD / HYP multi-label prediction
```

Recommended next implementation:

```text
src/models/fusion_concat.py
src/training/train_concat_fusion.py
configs/model_concat_fusion.yaml
scripts/06_train_concat_fusion_baseline.sh
tests/test_concat_fusion_baseline.py
```
