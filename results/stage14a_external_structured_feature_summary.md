# Stage 14A External Structured Feature Extraction Readiness Summary

Date: 2026-06-29

## Status

Stage 14A completed as a readiness audit. No external structured features were fabricated and no multimodal external validation was run.

## Result

| dataset   |   required_feature_count | existing_external_feature_table   |   existing_feature_count | exact_ptbxl_plus_feature_match   |   missing_required_features | ecgdeli_python_available   | ecgdeli_cli_available   | ecgdeli_r_available   | neurokit2_available   | can_generate_exact_ptbxl_plus_features_now   | can_run_full_multimodal_external_validation   | recommended_action                                             | blocking_issue                              |
|:----------|-------------------------:|:----------------------------------|-------------------------:|:---------------------------------|----------------------------:|:---------------------------|:------------------------|:----------------------|:----------------------|:---------------------------------------------|:----------------------------------------------|:---------------------------------------------------------------|:--------------------------------------------|
| cpsc2018  |                      531 |                                   |                        0 | False                            |                         531 | False                      | False                   | False                 | False                 | False                                        | False                                         | install_or_configure_exact_ecgdeli_feature_extraction_pipeline | ecgdeli_compatible_feature_pipeline_missing |
| chapman   |                      531 |                                   |                        0 | False                            |                         531 | False                      | False                   | False                 | False                 | False                                        | False                                         | install_or_configure_exact_ecgdeli_feature_extraction_pipeline | ecgdeli_compatible_feature_pipeline_missing |

## Key Conclusion

`external_structured_features_missing_for_multimodal` remains unresolved. The project cannot run fair concat or gated fusion on external datasets until an exact PTB-XL+ ecgdeli-compatible feature extraction pipeline is installed and validated.

## Generated Templates

- `data/processed/external/external_structured_feature_template_columns.txt`
- `data/processed/external/cpsc2018_structured_features_template.csv`
- `data/processed/external/chapman_structured_features_template.csv`

## Next Step

Install/configure an exact ecgdeli-compatible extractor or obtain external feature tables with the same 531 PTB-XL+ feature columns, then rerun this audit before multimodal external validation.
