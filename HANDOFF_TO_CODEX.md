# Handoff to Codex

## 1. Project Goal

The project goal is to build:

```text
An Interpretable Multimodal Decision-Support Framework for ECG-Based Cardiac Risk Stratification with Cross-Dataset Validation
```

The current engineering stage has not reached model development. The completed work is limited to raw data setup helper, local layout validation, data path discovery, data feasibility checking, and a PTB-XL preparation skeleton for labels, folds, and optional PTB-XL+ structured features.

## 2. Current Status

```text
Current status: waiting for raw PTB-XL data placement.
```

Model training cannot start because the required raw PTB-XL files are missing:

```text
data/raw/ptbxl/ptbxl_database.csv
data/raw/ptbxl/scp_statements.csv
data/raw/ptbxl/records100/
```

`records500/` is optional for now if the next stage uses only 100Hz waveforms.

## 3. Existing Completed Components

| File | Status |
|---|---|
| `docs/DATA_SETUP.md` | present |
| `configs/data_ptbxl.yaml` | present |
| `src/data/validate_local_data_layout.py` | present |
| `src/data/discover_data_paths.py` | present |
| `src/data/check_data_feasibility.py` | present |
| `src/data/prepare_ptbxl.py` | present |
| `src/data/prepare_ptbxl_plus.py` | present |
| `src/data/label_mapping.py` | present |
| `scripts/00b_validate_local_data_layout.sh` | present |
| `scripts/00c_print_physionet_download_commands.sh` | present |
| `scripts/00a_discover_data_paths.sh` | present |
| `scripts/00_check_data_feasibility.sh` | present |
| `scripts/01_prepare_ptbxl.sh` | present |
| `README.md` | present |

## 4. Reports Generated

| Report | Status |
|---|---|
| `results/local_data_layout_report.md` | present |
| `results/local_data_layout_summary.csv` | present |
| `results/data_path_discovery_report.md` | present |
| `results/data_path_discovery_candidates.csv` | present |
| `results/data_feasibility_report.md` | present |
| `results/data_feasibility_summary.csv` | present |
| `tables/table_label_distribution.csv` | present |
| `tables/table_structured_missingness.csv` | present |
| `tables/table_split_distribution.csv` | present |

## 5. Required Raw Data Layout

The user needs to place PTB-XL data as follows:

```text
data/raw/ptbxl/ptbxl_database.csv
data/raw/ptbxl/scp_statements.csv
data/raw/ptbxl/records100/
data/raw/ptbxl/records500/
```

Minimum requirement for a signal-only pipeline:

```text
data/raw/ptbxl/ptbxl_database.csv
data/raw/ptbxl/scp_statements.csv
data/raw/ptbxl/records100/
```

Optional PTB-XL+ structured features should be placed under:

```text
data/raw/ptbxl_plus/
```

## 6. Commands for Codex to Run After Data Placement

After the user places the raw files, Codex should run:

```bash
python -m pip install wfdb

bash scripts/00b_validate_local_data_layout.sh
bash scripts/00a_discover_data_paths.sh
bash scripts/00_check_data_feasibility.sh
bash scripts/01_prepare_ptbxl.sh
```

If `wfdb` installation is not possible, the validation scripts can still perform file existence checks, but waveform loading will not be validated.

## 7. Success Criteria

A successful PTB-XL setup should show:

```text
ptbxl_database.csv found: yes
scp_statements.csv found: yes
metadata rows: > 0
waveform files found: > 0
NORM / MI / STTC / CD / HYP positive_count > 0
strat_fold available
train / val / test split generated
```

If PTB-XL+ is also present, the reports should show:

```text
PTB-XL+ found: yes
aligned multimodal samples: > 0
structured feature columns: > 0
```

## 8. What Codex Should Not Do Yet

```text
Do not train models until PTB-XL metadata and waveform validation pass.
Do not implement ResNet or fusion model before Stage 0/1 succeeds.
Do not fabricate PTB-XL+ features.
Do not treat unrelated structured CSV files as PTB-XL+.
Do not generate empty processed files and call them successful.
```

## 9. Recommended Next Step

```text
Next step for Codex:
1. Check whether the user has placed PTB-XL raw files.
2. If raw files are missing, stop and ask user to place them.
3. If raw files exist, rerun Stage 0/1.
4. Only after Stage 0/1 succeeds, proceed to signal-only baseline.
5. Only after PTB-XL+ is found and aligned, proceed to multimodal baseline.
```
