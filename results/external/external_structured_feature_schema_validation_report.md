# External Structured Feature Schema Validation Report

Date: 2026-06-30

| dataset   | feature_table                                            | exists   |   n_rows |   n_columns |   required_feature_count |   matched_required_features |   missing_required_features |   extra_feature_columns | has_record_id   | has_source_dataset   | nonempty   | schema_exact_match   | can_run_multimodal_external_validation   | blocking_issue                            |
|:----------|:---------------------------------------------------------|:---------|---------:|------------:|-------------------------:|----------------------------:|----------------------------:|------------------------:|:----------------|:---------------------|:-----------|:---------------------|:-----------------------------------------|:------------------------------------------|
| cpsc2018  | data/processed/external/cpsc2018_structured_features.csv | False    |        0 |           0 |                      531 |                           0 |                         531 |                       0 | False           | False                | False      | False                | False                                    | external_structured_feature_table_missing |
| chapman   | data/processed/external/chapman_structured_features.csv  | False    |        0 |           0 |                      531 |                           0 |                         531 |                       0 | False           | False                | False      | False                | False                                    | external_structured_feature_table_missing |

A dataset is eligible for multimodal external validation only when the table is nonempty, has `record_id` and `source_dataset`, and exactly matches the frozen PTB-XL+ 531 structured feature schema.
