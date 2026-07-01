# External Validation Mode Decision

Generated date: 2026-06-29

| dataset   | external_data_found   | high_confidence_labels_available   | high_confidence_ptbxl_superclasses   | waveform_compatible   | structured_features_compatible   | recommended_external_validation_mode   | full_multimodal_external_validation_allowed   | signal_only_external_validation_allowed   | blocking_issue                                      | notes                                                          |
|:----------|:----------------------|:-----------------------------------|:-------------------------------------|:----------------------|:---------------------------------|:---------------------------------------|:----------------------------------------------|:------------------------------------------|:----------------------------------------------------|:---------------------------------------------------------------|
| cpsc2018  | True                  | True                               | CD;NORM                              | True                  | False                            | signal_only_main                       | False                                         | True                                      | external_structured_features_missing_for_multimodal | Readiness decision only; no external model evaluation was run. |
| chapman   | True                  | True                               | CD;HYP;MI;NORM                       | True                  | False                            | signal_only_main                       | False                                         | True                                      | external_structured_features_missing_for_multimodal | Readiness decision only; no external model evaluation was run. |

Allowed modes: `signal_only_main`, `multimodal_full`, `multimodal_missing_modality`, `external_feature_extraction_required`, `not_ready`.

Do not run fair concat or gated fusion externally unless structured feature compatibility is confirmed or a pre-specified missing-modality pathway exists.
