# Stage 14H PTB-XL ECGdeli Direct Recompute Audit Summary

Date: 2026-06-30

## Status

A small PTB-XL HR waveform sample was recomputed with the local MATLAB/ECGdeli direct candidate generator and compared against the official PTB-XL+ `ecgdeli_features.csv` table.

This is a reverse-engineering audit only. It does not establish an exact PTB-XL+ 531-feature recipe.

## Recompute Audit

|   ecg_id | status                              |   n_generated_direct_features |   n_expected_direct_features |   n_missing_direct_features | notes                                                                               |
|---------:|:------------------------------------|------------------------------:|-----------------------------:|----------------------------:|:------------------------------------------------------------------------------------|
|        1 | generated_direct_candidate_features |                           420 |                          420 |                           0 | PTB-XL HR waveform recomputed with local MATLAB/ECGdeli direct candidate generator. |
|        2 | generated_direct_candidate_features |                           420 |                          420 |                           0 | PTB-XL HR waveform recomputed with local MATLAB/ECGdeli direct candidate generator. |
|        3 | generated_direct_candidate_features |                           420 |                          420 |                           0 | PTB-XL HR waveform recomputed with local MATLAB/ECGdeli direct candidate generator. |

## Decision

| can_claim_exact_direct_420_recompute   | can_claim_exact_ptbxl_plus_recipe   | can_run_multimodal_external_validation   |   n_sample_records |   n_direct_features_compared |   n_direct_features_allclose |   median_feature_mae | blocking_issue                      | notes                                                                                                                               |
|:---------------------------------------|:------------------------------------|:-----------------------------------------|-------------------:|-----------------------------:|-----------------------------:|---------------------:|:------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------|
| False                                  | False                               | False                                    |                  3 |                          420 |                          138 |            0.0591017 | ptbxl_plus_exact_531_recipe_missing | Small-sample recomputation audit only; unresolved 111 features and any direct-feature discrepancies block exact 531-feature claims. |

## Largest Direct-Feature Differences

| feature           |   n_pairs |   official_nonmissing |   recomputed_nonmissing |   mean_abs_error |   median_abs_error |   max_abs_error | allclose_atol_1e_6   |
|:------------------|----------:|----------------------:|------------------------:|-----------------:|-------------------:|----------------:|:---------------------|
| QT_Int_III        |         3 |                     3 |                       3 |         216.606  |           210.727  |        326      | False                |
| T_DurFull_III     |         3 |                     3 |                       3 |         163.714  |           166.364  |        247.143  | False                |
| QT_Int_aVL        |         3 |                     3 |                       3 |         142.442  |           116.545  |        211.143  | False                |
| T_DurFull_V5      |         3 |                     3 |                       3 |         100.831  |            56.3636 |        212.857  | False                |
| QT_Int_aVF        |         3 |                     3 |                       3 |          96.8571 |           104.909  |        160.571  | False                |
| T_DurFull_aVF     |         3 |                     3 |                       3 |          92.7706 |            86.9091 |        126.857  | False                |
| T_DurFull_V6      |         3 |                     3 |                       3 |          90.9697 |            76.5455 |        148      | False                |
| T_DurFull_V3      |         3 |                     3 |                       3 |          87.4113 |            86      |        123.143  | False                |
| T_DurFull_aVF_iqr |         3 |                     3 |                       3 |          87.3333 |            62      |        187      | False                |
| T_DurFull_V4      |         3 |                     3 |                       3 |          79.8009 |            55.6364 |        128.857  | False                |
| T_DurFull_aVL     |         3 |                     3 |                       3 |          77.342  |            77.2727 |        126.571  | False                |
| T_DurFull_V1      |         3 |                     3 |                       3 |          76.4416 |            78.1818 |        102      | False                |
| T_DurFull_V4_iqr  |         3 |                     3 |                       3 |          75      |            96      |        127      | False                |
| T_DurFull_V2      |         3 |                     3 |                       3 |          71.5844 |            57.8182 |        132.571  | False                |
| QT_Int_Global     |         3 |                     3 |                       3 |          67.7922 |            82.9091 |         94.1818 | False                |

## Interpretation

- Local ECGdeli can recompute direct candidate features from PTB-XL HR waveforms.
- Numeric agreement with official PTB-XL+ must be audited before any exact-recipe claim.
- Complete 531-column external structured features remain blocked by unresolved QT_IntCorr, P_Morph, ST_Elev, and HA__Global definitions.

## Outputs

- `data/processed/ptbxl_ecgdeli_direct_recomputed_sample.csv`
- `tables/table_ptbxl_ecgdeli_direct_recompute_audit.csv`
- `tables/table_ptbxl_ecgdeli_direct_recompute_comparison.csv`
- `tables/table_ptbxl_ecgdeli_direct_recompute_decision.csv`
