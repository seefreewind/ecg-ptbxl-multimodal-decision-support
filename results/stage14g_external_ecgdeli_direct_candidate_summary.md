# Stage 14G External ECGdeli Direct Candidate Feature Summary

Date: 2026-06-30

## Status

A guarded candidate generator created only the 420 frozen-schema columns classified as `direct_ecgdeli` in Stage 14F. These files are incomplete candidate structured features and are not registered as official external multimodal inputs.

## Outputs

| dataset   |   n_rows |   n_columns |   n_direct_feature_columns | output                                                                 |
|:----------|---------:|------------:|---------------------------:|:-----------------------------------------------------------------------|
| cpsc2018  |        2 |         422 |                        420 | data/processed/external/cpsc2018_ecgdeli_direct_candidate_features.csv |
| chapman   |        2 |         422 |                        420 | data/processed/external/chapman_ecgdeli_direct_candidate_features.csv  |

## Audit

| dataset   | record_id   | status                              |   n_generated_direct_features |   n_expected_direct_features |   n_missing_direct_features | schema_exact_match   | blocking_issue                      | notes                                                                                             |
|:----------|:------------|:------------------------------------|------------------------------:|-----------------------------:|----------------------------:|:---------------------|:------------------------------------|:--------------------------------------------------------------------------------------------------|
| cpsc2018  | A0001       | generated_direct_candidate_features |                           420 |                          420 |                           0 | False                | ptbxl_plus_exact_531_recipe_missing | Direct ECGdeli candidate features only; unresolved 111 frozen PTB-XL+ features are not generated. |
| cpsc2018  | A0002       | generated_direct_candidate_features |                           420 |                          420 |                           0 | False                | ptbxl_plus_exact_531_recipe_missing | Direct ECGdeli candidate features only; unresolved 111 frozen PTB-XL+ features are not generated. |
| chapman   | JS00001     | generated_direct_candidate_features |                           420 |                          420 |                           0 | False                | ptbxl_plus_exact_531_recipe_missing | Direct ECGdeli candidate features only; unresolved 111 frozen PTB-XL+ features are not generated. |
| chapman   | JS00013     | generated_direct_candidate_features |                           420 |                          420 |                           0 | False                | ptbxl_plus_exact_531_recipe_missing | Direct ECGdeli candidate features only; unresolved 111 frozen PTB-XL+ features are not generated. |

## Decision

|   n_generated_direct_features |   n_required_features |   n_missing_required_features | can_run_multimodal_external_validation   | blocking_issue                      | notes                                                                                                                                                 |
|------------------------------:|----------------------:|------------------------------:|:-----------------------------------------|:------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------|
|                           420 |                   531 |                           111 | False                                    | ptbxl_plus_exact_531_recipe_missing | Candidate files contain only direct ECGdeli-derived frozen-schema columns and are intentionally not registered as external structured feature tables. |

## Interpretation

- The candidate files use real frozen PTB-XL+ column names for direct ECGdeli-derived features.
- They intentionally omit 111 unresolved required features.
- They must not be copied to `cpsc2018_structured_features.csv` or `chapman_structured_features.csv`.
- Full multimodal external validation remains blocked.

## Next Step

Resolve QT_IntCorr, P_Morph, ST_Elev, and HA__Global definitions before generating complete 531-column external structured feature tables.
