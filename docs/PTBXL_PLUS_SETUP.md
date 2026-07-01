# PTB-XL+ Setup Guide

## Purpose

PTB-XL+ provides structured ECG features that can be aligned to PTB-XL by ECG record ID. These features are required for structured-only and multimodal modeling.

PTB-XL+ is required for multimodal modeling. Without PTB-XL+, this project can only support signal-only PTB-XL experiments.

## Recommended Placement

Place PTB-XL+ files under:

```text
data/raw/ptbxl_plus/
```

Expected official PTB-XL+ structure:

```text
data/raw/ptbxl_plus/
├── features/
│   ├── 12sl_features.csv
│   ├── unig_features.csv
│   ├── ecgdeli_features.csv
│   └── feature_description.csv
├── labels/
│   ├── 12sl_statements.csv
│   ├── ptbxl_statements.csv
│   ├── snomed_description.csv
│   └── mapping/
├── median_beats/
├── fiducial_points/
├── RECORDS
├── LICENSE.txt
└── SHA256SUMS.txt
```

The PTB-XL main dataset remains under:

```text
data/raw/ptbxl/
```

## Accepted File Formats

PTB-XL+ candidate tables may use:

```text
.csv
.tsv
.parquet
.feather
.pkl
```

## Required ID Column

Each PTB-XL+ candidate must contain one supported ID column:

```text
ecg_id
record_id
id
ECG_ID
```

If the selected file uses `record_id`, `id`, or `ECG_ID`, the alignment script standardizes it to `ecg_id`.

## Structured Feature Criteria

Valid PTB-XL+ candidates should usually satisfy most of the following:

- more than 1000 rows
- more than 20 columns
- a supported ID column
- numeric structured ECG feature columns
- ECG feature keywords in column names, such as `qrs`, `qt`, `qtc`, `pr`, `rr`, `axis`, `amplitude`, `duration`, `interval`, or `rate`
- path or filename keywords such as `ptbxl`, `ptb-xl`, `ptbxl_plus`, `ptb-xl-plus`, `ecgdeli`, `unig`, or `features`

Generated project tables, small audit tables, `ptbxl_database.csv`, `scp_statements.csv`, and split/label files must not be treated as PTB-XL+.

## Leakage-safe PTB-XL+ file selection

Allowed feature tables:

- `features/12sl_features.csv`
- `features/unig_features.csv`
- `features/ecgdeli_features.csv`

Do not use as input features:

- `labels/12sl_statements.csv`
- `labels/ptbxl_statements.csv`
- `labels/snomed_description.csv`
- `labels/mapping/*.csv`

Rationale:

The project predicts PTB-XL diagnostic superclasses. Diagnostic statement tables contain label-like outputs from automated ECG interpretation systems or PTB-XL-derived statements. Using them as structured inputs would introduce label leakage and invalidate the multimodal comparison.

Preferred candidate order:

1. `features/ecgdeli_features.csv`
2. `features/12sl_features.csv`
3. `features/unig_features.csv`

`ecgdeli_features.csv` is the default first choice because it contains open ECG delineation and morphology features. `12sl_features.csv` and `unig_features.csv` may be useful for structured-only sensitivity analyses, but label and diagnostic statement files must remain excluded.

## Download and Placement Options

Do not force automated downloads inside project code. Use one of these approaches outside the validation scripts:

```bash
mkdir -p data/raw/ptbxl_plus

# Option A: manual download from PhysioNet PTB-XL+
# Place extracted folders so that data/raw/ptbxl_plus/features/ exists.

# Option B: wget, if network and PhysioNet access allow:
wget -r -N -c -np https://physionet.org/files/ptb-xl-plus/1.0.1/ -P data/raw/physionet_download/

# Option C: AWS public bucket:
aws s3 sync --no-sign-request s3://physionet-open/ptb-xl-plus/1.0.1/ data/raw/ptbxl_plus/
```

Network access, PhysioNet credential requirements, or local download failures should be reported as data-placement issues, not code failures.

## Validation Command

Run:

```bash
bash scripts/01b_validate_ptbxl_plus.sh
```

Expected outputs:

```text
results/ptbxl_plus_validation_report.md
results/ptbxl_plus_candidates.csv
```

## Alignment Command

Run alignment only after validation selects a real PTB-XL+ file:

```bash
bash scripts/01c_align_ptbxl_plus.sh
```

Expected outputs:

```text
data/processed/ptbxl_structured_features.csv
data/processed/ptbxl_multimodal_index.csv
data/processed/structured_feature_names.txt
tables/table_ptbxl_plus_missingness.csv
tables/table_ptbxl_plus_alignment.csv
results/ptbxl_plus_alignment_report.md
```

## Success Criteria

PTB-XL+ alignment is considered ready only when:

```text
aligned rows > 10000
structured feature columns > 20
```

## Failure Reporting

If PTB-XL+ is missing, the validation report must state:

```text
PTB-XL+ structured features are still missing. Multimodal modeling is not allowed yet.
```

If alignment rows are low or no numeric structured features are found, do not continue to multimodal modeling. Report the blocking issue and fix PTB-XL+ placement, ID columns, or file selection first.
