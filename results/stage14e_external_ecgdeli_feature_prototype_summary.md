# Stage 14E External ECGdeli Feature Prototype Summary

Date: 2026-06-30

## Status

A small ECGdeli-based external feature extraction prototype was run on two main-analysis records per external dataset. This stage verifies that external WFDB records can be passed through ECGdeli and summarized, but it does not reproduce the frozen PTB-XL+ 531-column feature schema.

## Outputs

| dataset   |   n_rows |   n_columns |   n_feature_columns | output                                                          | schema_exact_match   |
|:----------|---------:|------------:|--------------------:|:----------------------------------------------------------------|:---------------------|
| cpsc2018  |        2 |         458 |                 456 | data/processed/external/cpsc2018_ecgdeli_features_prototype.csv | False                |
| chapman   |        2 |         458 |                 456 | data/processed/external/chapman_ecgdeli_features_prototype.csv  | False                |

## Audit

| dataset   | record_id   | record_base                                                                        | status                         |   n_feature_columns | schema_exact_match   | blocking_issue                      | notes                                                                |   matched_required_features |   required_feature_count |
|:----------|:------------|:-----------------------------------------------------------------------------------|:-------------------------------|--------------------:|:---------------------|:------------------------------------|:---------------------------------------------------------------------|----------------------------:|-------------------------:|
| cpsc2018  | A0001       | /Users/zy/csbj/新高分思路/data/raw/external/cpsc2018/cpsc_2018/g1/A0001                 | generated_exploratory_features |                 456 | False                | ptbxl_plus_exact_531_recipe_missing | Exploratory ECGdeli aggregation only; not frozen PTB-XL+ 531 schema. |                           0 |                      531 |
| cpsc2018  | A0002       | /Users/zy/csbj/新高分思路/data/raw/external/cpsc2018/cpsc_2018/g1/A0002                 | generated_exploratory_features |                 456 | False                | ptbxl_plus_exact_531_recipe_missing | Exploratory ECGdeli aggregation only; not frozen PTB-XL+ 531 schema. |                           0 |                      531 |
| chapman   | JS00001     | /Users/zy/csbj/新高分思路/data/raw/external/chapman_shaoxing/WFDBRecords/01/010/JS00001 | generated_exploratory_features |                 456 | False                | ptbxl_plus_exact_531_recipe_missing | Exploratory ECGdeli aggregation only; not frozen PTB-XL+ 531 schema. |                           0 |                      531 |
| chapman   | JS00013     | /Users/zy/csbj/新高分思路/data/raw/external/chapman_shaoxing/WFDBRecords/01/010/JS00013 | generated_exploratory_features |                 456 | False                | ptbxl_plus_exact_531_recipe_missing | Exploratory ECGdeli aggregation only; not frozen PTB-XL+ 531 schema. |                           0 |                      531 |

## Interpretation

- The generated files are exploratory prototype features and use `ecgdeli_proto_*` column names.
- They must not be used as fair concat or gated-fusion external inputs.
- The remaining blocker is the missing exact PTB-XL+ ECGdeli 531-feature aggregation recipe.

## Next Step

Map the PTB-XL+ frozen feature names to ECGdeli amplitude, interval, morphology, and summary-statistic definitions, or obtain the official aggregation recipe. Only after schema validation passes should multimodal external validation be run.
