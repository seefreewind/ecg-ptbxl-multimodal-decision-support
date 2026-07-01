# ECG PTB-XL Stage 0/1 Data Preparation

This repository section supports the first engineering stage for:

**An Interpretable Multimodal Decision-Support Framework for ECG-Based Cardiac Risk Stratification with Cross-Dataset Validation**

This stage only checks data feasibility and prepares PTB-XL / PTB-XL+ data files. It does not train models, implement ResNet or Transformer, run SHAP or Grad-CAM, perform DCA, implement uncertainty estimation, write the paper body, or download large external datasets.

## Data placement

By default, place PTB-XL files under:

```text
data/raw/ptbxl/ptbxl_database.csv
data/raw/ptbxl/scp_statements.csv
data/raw/ptbxl/<WFDB waveform files referenced by filename_lr/filename_hr>
```

Place PTB-XL+ structured feature files under:

```text
data/raw/ptbxl_plus/<structured feature files>
```

The PTB-XL+ feature file can be one or more `.csv`, `.tsv`, `.parquet`, `.feather`, or `.pkl` files. The scripts try to identify common ECG ID columns such as `ecg_id`, `record_id`, `id`, and `ECG_ID`.

If your data are stored elsewhere, edit:

```text
configs/data_ptbxl.yaml
```

## Before Stage 0: Prepare raw data

1. Read `docs/DATA_SETUP.md`.
2. Place PTB-XL files under `data/raw/ptbxl/`.
3. Optionally place PTB-XL+ files under `data/raw/ptbxl_plus/`.
4. Run:

```bash
bash scripts/00b_validate_local_data_layout.sh
bash scripts/00a_discover_data_paths.sh
bash scripts/00_check_data_feasibility.sh
bash scripts/01_prepare_ptbxl.sh
```

If PTB-XL metadata or SCP statements are still missing after validation, do not run Stage 1 yet. Fix the raw data placement first.

To print suggested PhysioNet download and placement commands without downloading data automatically, run:

```bash
bash scripts/00c_print_physionet_download_commands.sh
```

## Stage 0: Data Feasibility Check

Run:

```bash
bash scripts/00_check_data_feasibility.sh
```

Outputs:

* results/data_feasibility_report.md
* results/data_feasibility_summary.csv
* tables/table_label_distribution.csv
* tables/table_structured_missingness.csv
* tables/table_split_distribution.csv

The report checks PTB-XL metadata, waveform file availability, PTB-XL diagnostic superclass labels, PTB-XL+ structured features, ECG ID alignment, and official fold splits.

## Stage 1: PTB-XL Data Preparation

Run:

```bash
bash scripts/01_prepare_ptbxl.sh
```

Outputs:

* data/processed/ptbxl_labels.csv
* data/splits/ptbxl_train.csv
* data/splits/ptbxl_val.csv
* data/splits/ptbxl_test.csv
* data/processed/ptbxl_structured_features.csv, if PTB-XL+ is available
* data/processed/structured_feature_names.txt, if PTB-XL+ is available
* tables/table_structured_features_overview.csv

The official PTB-XL folds are used directly:

* train: folds 1-8
* val: fold 9
* test: fold 10

If PTB-XL+ is not available, Stage 1 keeps the signal-only PTB-XL labels and splits and prints a warning instead of failing the whole script.
