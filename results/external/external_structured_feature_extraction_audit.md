# External Structured Feature Extraction Audit

Date: 2026-06-29

## Audit Table

| dataset   |   required_feature_count | existing_external_feature_table   |   existing_feature_count | exact_ptbxl_plus_feature_match   |   missing_required_features | ecgdeli_python_available   | ecgdeli_cli_available   | ecgdeli_r_available   | neurokit2_available   | can_generate_exact_ptbxl_plus_features_now   | can_run_full_multimodal_external_validation   | recommended_action                                             | blocking_issue                              |
|:----------|-------------------------:|:----------------------------------|-------------------------:|:---------------------------------|----------------------------:|:---------------------------|:------------------------|:----------------------|:----------------------|:---------------------------------------------|:----------------------------------------------|:---------------------------------------------------------------|:--------------------------------------------|
| cpsc2018  |                      531 |                                   |                        0 | False                            |                         531 | False                      | False                   | False                 | False                 | False                                        | False                                         | install_or_configure_exact_ecgdeli_feature_extraction_pipeline | ecgdeli_compatible_feature_pipeline_missing |
| chapman   |                      531 |                                   |                        0 | False                            |                         531 | False                      | False                   | False                 | False                 | False                                        | False                                         | install_or_configure_exact_ecgdeli_feature_extraction_pipeline | ecgdeli_compatible_feature_pipeline_missing |

## Interpretation

Full multimodal external validation remains blocked unless external structured features exactly match the PTB-XL+ selected 531 ecgdeli feature names and definitions.

NeuroKit2-style features may be useful for a separate exploratory model, but they are not treated as compatible with the frozen fair concat or gated fusion models.
