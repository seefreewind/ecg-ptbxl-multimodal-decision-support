# PTB-XL+ Validation Report

## 1. Search Scope

- /Users/zy/Documents/ecg/data/raw/ptbxl_plus

## 2. Candidate Files

| candidate_path                                                               | relative_path                    | file_type   | role                    | allowed_as_structured_input   | excluded   | exclude_reason                                                      |   n_rows |   n_columns | id_column   |   numeric_columns |   non_numeric_columns |   ecg_feature_keyword_count |   label_leakage_keyword_count |   aligned_preview_rows |   score | selected   | error   |
|:-----------------------------------------------------------------------------|:---------------------------------|:------------|:------------------------|:------------------------------|:-----------|:--------------------------------------------------------------------|---------:|------------:|:------------|------------------:|----------------------:|----------------------------:|------------------------------:|-----------------------:|--------:|:-----------|:--------|
| /Users/zy/Documents/ecg/data/raw/ptbxl_plus/features/12sl_features.csv       | features/12sl_features.csv       | csv         | allowed_feature_table   | True                          | False      |                                                                     |     5000 |         783 | ecg_id      |               783 |                     0 |                           5 |                             0 |                   5000 |     365 | False      |         |
| /Users/zy/Documents/ecg/data/raw/ptbxl_plus/features/ecgdeli_features.csv    | features/ecgdeli_features.csv    | csv         | allowed_feature_table   | True                          | False      |                                                                     |     5000 |         532 | ecg_id      |               532 |                     0 |                           4 |                             0 |                   5000 |     460 | True       |         |
| /Users/zy/Documents/ecg/data/raw/ptbxl_plus/features/feature_description.csv | features/feature_description.csv | csv         | metadata_or_description | False                         | True       | Feature description metadata is not a per-record model input table. |      195 |          10 | id          |                 2 |                     8 |                           0 |                             0 |                      0 |      30 | False      |         |
| /Users/zy/Documents/ecg/data/raw/ptbxl_plus/features/unig_features.csv       | features/unig_features.csv       | csv         | allowed_feature_table   | True                          | False      |                                                                     |     5000 |         749 | ecg_id      |               749 |                     0 |                           5 |                             0 |                   5000 |     265 | False      |         |

## 3. Selected Feature File

/Users/zy/Documents/ecg/data/raw/ptbxl_plus/features/ecgdeli_features.csv

## 4. ID Column Detection

ecg_id

## 5. Feature Type Summary

- allowed feature files: features/12sl_features.csv, features/ecgdeli_features.csv, features/unig_features.csv
- excluded files: features/feature_description.csv
- high leakage risk files: none

## 6. Missingness Summary

Missingness is audited during alignment after full selected-file loading.

## 7. Alignment Readiness

ready for alignment

## 8. Blocking Issue

none

## 9. Recommended Next Action

Run `bash scripts/01c_align_ptbxl_plus.sh`.
