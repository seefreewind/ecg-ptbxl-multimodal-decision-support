# Stage 3 PTB-XL+ Summary

## 1. PTB-XL+ Raw File Status

- features directory found: no
- ecgdeli_features.csv found: no
- 12sl_features.csv found: no
- unig_features.csv found: no
- labels directory found: no

Expected leakage-safe feature files:

```text
data/raw/ptbxl_plus/features/ecgdeli_features.csv
data/raw/ptbxl_plus/features/12sl_features.csv
data/raw/ptbxl_plus/features/unig_features.csv
```

## 2. File Role and Leakage Audit

- allowed feature files: none found locally
- excluded label/statement files: none found locally
- high leakage risk files: none found locally

The static leakage audit table was created at:

```text
tables/table_ptbxl_plus_file_audit.csv
```

It explicitly permits:

- `features/ecgdeli_features.csv`
- `features/12sl_features.csv`
- `features/unig_features.csv`

It explicitly excludes:

- `labels/12sl_statements.csv`
- `labels/ptbxl_statements.csv`
- `labels/snomed_description.csv`
- `labels/mapping/*.csv`

Rationale: diagnostic statement files, SNOMED mappings, and PTB-XL-derived annotations may contain target-like information and must not be used as structured input features.

## 3. Selected Feature File

- selected: none
- reason: no PTB-XL+ structured feature files were found under `data/raw/ptbxl_plus/`
- fallback used: none

Preferred selection order after PTB-XL+ is placed:

1. `features/ecgdeli_features.csv`
2. `features/12sl_features.csv`
3. `features/unig_features.csv`

## 4. Alignment Result

- PTB-XL rows: 21799
- PTB-XL+ rows: 0
- aligned rows: 0
- alignment rate: 0
- raw feature columns: 0
- kept feature columns: 0
- dropped feature columns: 0

Alignment was not run because validation did not select a leakage-safe PTB-XL+ feature file.

## 5. Missingness

- features dropped due to missingness > 40%: not applicable
- top 20 missingness features: not applicable

Missingness auditing will run after a selected feature table is available.

## 6. Readiness Decision

Blocked: PTB-XL+ files missing

The project is not ready for structured-only baseline. It remains at the signal-only strong baseline stage until PTB-XL+ is downloaded/extracted and validated.

## 7. Next Step

Download or extract PTB-XL+ into:

```text
data/raw/ptbxl_plus/
```

The path should contain:

```text
data/raw/ptbxl_plus/features/ecgdeli_features.csv
```

Then run:

```bash
bash scripts/01b_validate_ptbxl_plus.sh
```

If validation selects a leakage-safe file under `features/`, run:

```bash
bash scripts/01c_align_ptbxl_plus.sh
```

Proceed to structured-only baseline only if:

```text
aligned_rows > 10000
kept_feature_columns > 20
selected feature file is under features/
selected feature file is not under labels/
no diagnostic statement columns kept
```
