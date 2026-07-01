# PTB-XL / PTB-XL+ Data Setup Guide

## 1. Required PTB-XL files

Download PTB-XL from PhysioNet and place the files in this project as follows:

```text
data/raw/ptbxl/ptbxl_database.csv
data/raw/ptbxl/scp_statements.csv
data/raw/ptbxl/records100/
data/raw/ptbxl/records500/
```

The minimum requirement for a signal-only baseline is:

```text
data/raw/ptbxl/ptbxl_database.csv
data/raw/ptbxl/scp_statements.csv
data/raw/ptbxl/records100/
```

Inside `records100/`, the WFDB files should look like this:

```text
data/raw/ptbxl/records100/00000/00001_lr.dat
data/raw/ptbxl/records100/00000/00001_lr.hea
```

`ptbxl_database.csv` usually stores waveform paths without file extensions, for example `records100/00000/00001_lr`. The validation scripts therefore check the base path and the `.hea` / `.dat` files.

## 2. Optional PTB-XL+ files

For multimodal modeling, place PTB-XL+ structured ECG feature files under:

```text
data/raw/ptbxl_plus/
```

PTB-XL+ files may be `.csv`, `.tsv`, `.parquet`, `.feather`, or `.pkl` tables. Valid candidates should contain ECG IDs and structured ECG features such as intervals, axes, amplitudes, durations, or rates.

Do not treat unrelated files such as `structured_audit`, `confirmed_pair_structured_audit_packet.csv`, or other project audit tables as PTB-XL+ data.

## 3. Recommended verification command

After placing the raw data, run:

```bash
bash scripts/00b_validate_local_data_layout.sh
bash scripts/00a_discover_data_paths.sh
bash scripts/00_check_data_feasibility.sh
bash scripts/01_prepare_ptbxl.sh
```

If `ptbxl_database.csv` or `scp_statements.csv` is still missing, run only the first three commands and fix the raw data placement before Stage 1.

## 4. Success criteria

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

If PTB-XL+ is available, the reports should also show:

```text
PTB-XL+ found: yes
aligned multimodal samples: > 0
structured feature columns: > 0
```

## 5. Download command helper

The project includes a command helper that prints suggested PhysioNet download and placement commands without downloading data automatically:

```bash
bash scripts/00c_print_physionet_download_commands.sh
```

PhysioNet access may require network access, login, credential setup, or license acceptance. If automated download fails, download manually and place or symlink the files into the paths shown above.
