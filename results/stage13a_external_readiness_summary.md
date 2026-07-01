# Stage 13A External Validation Readiness Summary

Date: 2026-06-29

## 1. Stage Status

- completed
- This stage is a readiness audit only. No formal external validation was run.

## 2. External Dataset Availability

### CPSC2018

- availability: found
- root path: `/Users/zy/csbj/新高分思路/data/raw/external/cpsc2018`
- waveform files: 20660
- label files: 10330
- metadata files: 10330
- draft high-confidence mapped labels: CD, NORM
- medium-confidence labels: STD
- excluded/low-confidence labels: STE, AF, PAC, PVC
- PTB-XL superclasses not safely covered by high-confidence draft mapping: HYP, MI, STTC
- lead count: 12
- sampling rate: 500.0
- duration: 14.0
- compatible with signal-only model: True
- structured features available: False
- full multimodal allowed: False
- recommended mode: `signal_only_main`
- blocking issue: external_structured_features_missing_for_multimodal

### Chapman-Shaoxing

- availability: found
- root path: `/Users/zy/csbj/新高分思路/data/raw/external/chapman_shaoxing`
- waveform files: 90304
- label files: 1
- metadata files: 45152
- draft high-confidence mapped labels: CD, HYP, MI, NORM
- medium-confidence labels: Sinus rhythm, ST-T abnormality
- excluded/low-confidence labels: Atrial fibrillation
- PTB-XL superclasses not safely covered by high-confidence draft mapping: STTC
- lead count: 12
- sampling rate: 500.0
- duration: 10.0
- compatible with signal-only model: True
- structured features available: False
- full multimodal allowed: False
- recommended mode: `signal_only_main`
- blocking issue: external_structured_features_missing_for_multimodal

## 3. Label Mapping Audit

- High-confidence labels may enter main external validation only after actual external label files confirm the same semantics.
- Medium-confidence labels are sensitivity-analysis only.
- Low-confidence and excluded labels must not enter main external validation.
- Main external validation may use a subset of PTB-XL superclasses.

## 4. Waveform Compatibility

| dataset   |   n_records_checked |   lead_count | lead_order_detected                    |   sampling_rate_detected |   duration_detected |   target_sampling_rate |   target_length | requires_resampling   | requires_padding_or_cropping   | compatible_with_signal_model   |   blocking_issue | notes                                      |
|:----------|--------------------:|-------------:|:---------------------------------------|-------------------------:|--------------------:|-----------------------:|----------------:|:----------------------|:-------------------------------|:-------------------------------|-----------------:|:-------------------------------------------|
| cpsc2018  |                  11 |           12 | I,II,III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6 |                      500 |                  14 |                    100 |            1000 | True                  | True                           | True                           |              nan | Compatible after documented preprocessing. |
| chapman   |                  10 |           12 | I,II,III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6 |                      500 |                  10 |                    100 |            1000 | True                  | False                          | True                           |              nan | Compatible after documented preprocessing. |

## 5. Structured Feature Compatibility

| dataset   | has_external_structured_features   |   feature_source |   n_features | matches_ptbxl_plus_features   |   missing_required_features | can_run_signal_only   | can_run_fair_concat   | can_run_gated_fusion   | requires_feature_extraction   | recommended_external_validation_mode   | blocking_issue                                      |
|:----------|:-----------------------------------|-----------------:|-------------:|:------------------------------|----------------------------:|:----------------------|:----------------------|:-----------------------|:------------------------------|:---------------------------------------|:----------------------------------------------------|
| cpsc2018  | False                              |              nan |            0 | False                         |                         531 | True                  | False                 | False                  | True                          | signal_only_main                       | external_structured_features_missing_for_multimodal |
| chapman   | False                              |              nan |            0 | False                         |                         531 | True                  | False                 | False                  | True                          | signal_only_main                       | external_structured_features_missing_for_multimodal |

## 6. Recommended External Validation Mode

| dataset   | external_data_found   | high_confidence_labels_available   | high_confidence_ptbxl_superclasses   | waveform_compatible   | structured_features_compatible   | recommended_external_validation_mode   | full_multimodal_external_validation_allowed   | signal_only_external_validation_allowed   | blocking_issue                                      | notes                                                          |
|:----------|:----------------------|:-----------------------------------|:-------------------------------------|:----------------------|:---------------------------------|:---------------------------------------|:----------------------------------------------|:------------------------------------------|:----------------------------------------------------|:---------------------------------------------------------------|
| cpsc2018  | True                  | True                               | CD;NORM                              | True                  | False                            | signal_only_main                       | False                                         | True                                      | external_structured_features_missing_for_multimodal | Readiness decision only; no external model evaluation was run. |
| chapman   | True                  | True                               | CD;HYP;MI;NORM                       | True                  | False                            | signal_only_main                       | False                                         | True                                      | external_structured_features_missing_for_multimodal | Readiness decision only; no external model evaluation was run. |

## 7. Blocking Issues

- external_structured_features_missing_for_multimodal
- external_structured_features_missing_for_multimodal

## 8. What Must Not Be Claimed Yet

- no external generalization claim
- no clinical-readiness claim
- no multimodal external validation claim unless structured features are compatible

## 9. Next Recommended Step

- proceed to signal-only external validation for compatible datasets only.
