# Stage 14F PTB-XL+ ECGdeli Feature Mapping Audit Summary

Date: 2026-06-30

## Status

The frozen PTB-XL+ 531 structured feature names were parsed and compared against the audited ECGdeli MATLAB outputs: amplitude features, interval features, synchronized interval features, and P-wave morphology.

This is a schema and recipe audit only. It does not generate exact PTB-XL+ external structured features.

## Derivability Summary

| derivability                 |   n_features |   percent_of_531 |
|:-----------------------------|-------------:|-----------------:|
| direct_ecgdeli               |          420 |            79.1  |
| requires_extra_formula       |           36 |             6.78 |
| requires_morphology_function |           36 |             6.78 |
| unknown_recipe               |           39 |             7.34 |

## Decision

| can_generate_exact_531_features   | can_run_multimodal_external_validation   |   direct_or_formula_candidate_features |   unknown_recipe_features | blocking_issue                      | notes                                                                                                     |
|:----------------------------------|:-----------------------------------------|---------------------------------------:|--------------------------:|:------------------------------------|:----------------------------------------------------------------------------------------------------------|
| False                             | False                                    |                                    492 |                        39 | ptbxl_plus_exact_531_recipe_missing | This is a feature-name mapping audit only; it does not establish exact PTB-XL+ aggregation compatibility. |

## Example Mappings

| ptbxl_plus_feature   | derivability                 | ecgdeli_source                                           | notes                                                                                                                  |
|:---------------------|:-----------------------------|:---------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------|
| PQ_Int_I             | direct_ecgdeli               | Timing_feature_12leads(:,:,4)                            | Appears derivable from ECGdeli interval: PQ interval; exact filtering and aggregation must still match PTB-XL+.        |
| PQ_Int_I_iqr         | direct_ecgdeli               | Timing_feature_12leads(:,:,4)                            | Appears derivable from ECGdeli interval: PQ interval; exact filtering and aggregation must still match PTB-XL+.        |
| PQ_Int_I_count       | direct_ecgdeli               | Timing_feature_12leads(:,:,4)                            | Appears derivable from ECGdeli interval: PQ interval; exact filtering and aggregation must still match PTB-XL+.        |
| PQ_Int_II            | direct_ecgdeli               | Timing_feature_12leads(:,:,4)                            | Appears derivable from ECGdeli interval: PQ interval; exact filtering and aggregation must still match PTB-XL+.        |
| PQ_Int_II_iqr        | direct_ecgdeli               | Timing_feature_12leads(:,:,4)                            | Appears derivable from ECGdeli interval: PQ interval; exact filtering and aggregation must still match PTB-XL+.        |
| PQ_Int_II_count      | direct_ecgdeli               | Timing_feature_12leads(:,:,4)                            | Appears derivable from ECGdeli interval: PQ interval; exact filtering and aggregation must still match PTB-XL+.        |
| PQ_Int_III           | direct_ecgdeli               | Timing_feature_12leads(:,:,4)                            | Appears derivable from ECGdeli interval: PQ interval; exact filtering and aggregation must still match PTB-XL+.        |
| PQ_Int_III_iqr       | direct_ecgdeli               | Timing_feature_12leads(:,:,4)                            | Appears derivable from ECGdeli interval: PQ interval; exact filtering and aggregation must still match PTB-XL+.        |
| P_Morph_I            | requires_morphology_function | Get_P_Morphology                                         | Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed       |
| P_Morph_I_iqr        | requires_morphology_function | Get_P_Morphology                                         | Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed       |
| P_Morph_I_count      | requires_morphology_function | Get_P_Morphology                                         | Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed       |
| P_Morph_II           | requires_morphology_function | Get_P_Morphology                                         | Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed       |
| P_Morph_II_iqr       | requires_morphology_function | Get_P_Morphology                                         | Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed       |
| P_Morph_II_count     | requires_morphology_function | Get_P_Morphology                                         | Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed       |
| P_Morph_III          | requires_morphology_function | Get_P_Morphology                                         | Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed       |
| P_Morph_III_iqr      | requires_morphology_function | Get_P_Morphology                                         | Get_P_Morphology can emit P morphology classes, but exact PTB-XL+ aggregation and coding rules must be confirmed       |
| QT_IntCorr_I         | requires_extra_formula       | Timing_feature_12leads(:,:,6) plus RR/correction formula | leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule |
| QT_IntCorr_I_iqr     | requires_extra_formula       | Timing_feature_12leads(:,:,6) plus RR/correction formula | leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule |
| QT_IntCorr_I_count   | requires_extra_formula       | Timing_feature_12leads(:,:,6) plus RR/correction formula | leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule |
| QT_IntCorr_II        | requires_extra_formula       | Timing_feature_12leads(:,:,6) plus RR/correction formula | leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule |
| QT_IntCorr_II_iqr    | requires_extra_formula       | Timing_feature_12leads(:,:,6) plus RR/correction formula | leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule |
| QT_IntCorr_II_count  | requires_extra_formula       | Timing_feature_12leads(:,:,6) plus RR/correction formula | leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule |
| QT_IntCorr_III       | requires_extra_formula       | Timing_feature_12leads(:,:,6) plus RR/correction formula | leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule |
| QT_IntCorr_III_iqr   | requires_extra_formula       | Timing_feature_12leads(:,:,6) plus RR/correction formula | leadwise QT correction formula is not emitted by ECGdeli interval extractor and needs an exact PTB-XL+ correction rule |
| ST_Elev_I            | unknown_recipe               |                                                          | ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors                               |
| ST_Elev_I_iqr        | unknown_recipe               |                                                          | ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors                               |
| ST_Elev_I_count      | unknown_recipe               |                                                          | ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors                               |
| ST_Elev_II           | unknown_recipe               |                                                          | ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors                               |
| ST_Elev_II_iqr       | unknown_recipe               |                                                          | ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors                               |
| ST_Elev_II_count     | unknown_recipe               |                                                          | ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors                               |
| ST_Elev_III          | unknown_recipe               |                                                          | ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors                               |
| ST_Elev_III_iqr      | unknown_recipe               |                                                          | ST elevation feature is not emitted by the audited ECGdeli amplitude/interval extractors                               |

## Interpretation

- Many amplitude and interval feature names appear structurally derivable from ECGdeli outputs.
- QT correction, P morphology, ST elevation, and HA features still require exact PTB-XL+ definitions or additional audited implementation rules.
- Even direct candidates still require exact agreement on filtering, units, lead ordering, beat inclusion, summary statistics, and missing-value handling.
- Therefore, full multimodal external validation remains blocked.

## Next Step

Implement a guarded candidate generator only for direct ECGdeli features, compare its columns against the frozen 531 schema, and leave unresolved columns missing until the exact PTB-XL+ recipe is obtained or faithfully reconstructed.
