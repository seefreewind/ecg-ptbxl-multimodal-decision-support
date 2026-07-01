# Stage 14I PTB-XL ECGdeli Direct Discrepancy Diagnosis Summary

Date: 2026-06-30

## Status

The Stage 14H direct-feature recomputation audit was grouped by ECG feature family and summary statistic to identify where local ECGdeli-derived values diverge most from official PTB-XL+ `ecgdeli_features.csv`.

## Decision

| direct_420_exact_enough_for_recipe_claim   | can_run_multimodal_external_validation   | worst_family   |   families_with_any_discrepancy | blocking_issue                                                         | notes                                                                                                                              |
|:-------------------------------------------|:-----------------------------------------|:---------------|--------------------------------:|:-----------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------|
| False                                      | False                                    | T_DurFull:mean |                              32 | direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing | Direct candidate feature names are not sufficient; numeric definitions and remaining 111 features still need exact reconstruction. |

## Family-Level Discrepancy Summary

| base_feature     | summary_statistic   |   n_features |   n_pairs |   n_allclose |   median_mean_abs_error |   max_mean_abs_error |   median_max_abs_error |   allclose_rate |
|:-----------------|:--------------------|-------------:|----------:|-------------:|------------------------:|---------------------:|-----------------------:|----------------:|
| T_DurFull        | mean                |           12 |        36 |            0 |              78.5714    |          163.714     |            126.714     |               0 |
| QT_IntFramingham | mean                |            1 |         3 |            0 |              67.7282    |           67.7282    |            103.322     |               0 |
| QT_Int           | mean                |           13 |        39 |            0 |              56.961     |          216.606     |             95.0909    |               0 |
| T_Dur            | mean                |            1 |         3 |            0 |              55.8268    |           55.8268    |             57.4545    |               0 |
| QT_Int           | iqr                 |           13 |        39 |            0 |              43.6667    |           63.3333    |             69         |               0 |
| T_DurFull        | iqr                 |           12 |        36 |            0 |              39.8333    |           87.3333    |             58.5       |               0 |
| QT_IntFramingham | iqr                 |            1 |         3 |            0 |              38.8545    |           38.8545    |             56.9665    |               0 |
| T_Dur            | iqr                 |            1 |         3 |            0 |              36.6667    |           36.6667    |            101         |               0 |
| P_Dur            | mean                |            1 |         3 |            0 |              31.7636    |           31.7636    |             54         |               0 |
| P_Dur            | iqr                 |            1 |         3 |            0 |              25.3333    |           25.3333    |             41         |               0 |
| PQ_Int           | mean                |           13 |        39 |            0 |              16.8918    |           33.1948    |             30.9091    |               0 |
| PR_Int           | mean                |           13 |        39 |            0 |              16.8485    |           35.3506    |             32.1818    |               0 |
| PR_Int           | iqr                 |           13 |        39 |            0 |              16         |           26.6667    |             27         |               0 |
| P_DurFull        | iqr                 |           12 |        36 |            0 |              15.6667    |           25.3333    |             30         |               0 |
| PQ_Int           | iqr                 |           13 |        39 |            0 |              15.6667    |           26         |             29         |               0 |
| P_DurFull        | mean                |           12 |        36 |            0 |              14.4459    |           21.8701    |             26.4416    |               0 |
| RR_Mean          | mean                |            1 |         3 |            0 |              11.3939    |           11.3939    |             20         |               0 |
| RR_Mean          | iqr                 |            1 |         3 |            0 |              10.1667    |           10.1667    |             21         |               0 |
| QRS_Dur          | mean                |           13 |        39 |            0 |               2.25108   |            4.99567   |              5.27273   |               0 |
| QRS_Dur          | iqr                 |           13 |        39 |            0 |               1.66667   |           13.6667    |              3         |               0 |
| QT_IntFramingham | count               |            1 |         3 |            0 |               1         |            1         |              1         |               0 |
| RR_Mean          | count               |            1 |         3 |            0 |               1         |            1         |              1         |               0 |
| R_Amp            | mean                |           12 |        36 |            0 |               0.0819166 |            0.924344  |              0.154185  |               0 |
| T_Amp            | mean                |           12 |        36 |            0 |               0.0664727 |            0.224784  |              0.120549  |               0 |
| T_Amp            | iqr                 |           12 |        36 |            0 |               0.0654865 |            0.143246  |              0.128326  |               0 |
| P_Amp            | iqr                 |           12 |        36 |            0 |               0.0579372 |            0.103776  |              0.0956757 |               0 |
| S_Amp            | iqr                 |           12 |        36 |            0 |               0.0570392 |            0.160167  |              0.0976733 |               0 |
| R_Amp            | iqr                 |           12 |        36 |            0 |               0.0549521 |            0.237449  |              0.0845357 |               0 |
| S_Amp            | mean                |           12 |        36 |            0 |               0.0472887 |            0.178859  |              0.101485  |               0 |
| Q_Amp            | iqr                 |           12 |        36 |            0 |               0.0453044 |            0.12199   |              0.0682781 |               0 |
| Q_Amp            | mean                |           12 |        36 |            0 |               0.0367666 |            0.656534  |              0.0624458 |               0 |
| P_Amp            | mean                |           12 |        36 |            0 |               0.0334218 |            0.0527306 |              0.0463074 |               0 |
| PQ_Int           | count               |           13 |        39 |           13 |               0         |            0         |              0         |               1 |
| PR_Int           | count               |           13 |        39 |           13 |               0         |            0         |              0         |               1 |
| P_Amp            | count               |           12 |        36 |           12 |               0         |            0         |              0         |               1 |
| P_Dur            | count               |            1 |         3 |            1 |               0         |            0         |              0         |               1 |
| P_DurFull        | count               |           12 |        36 |           12 |               0         |            0         |              0         |               1 |
| QRS_Dur          | count               |           13 |        39 |           13 |               0         |            0         |              0         |               1 |
| QT_Int           | count               |           13 |        39 |           13 |               0         |            0         |              0         |               1 |
| Q_Amp            | count               |           12 |        36 |           12 |               0         |            0         |              0         |               1 |
| R_Amp            | count               |           12 |        36 |           12 |               0         |            0         |              0         |               1 |
| S_Amp            | count               |           12 |        36 |           12 |               0         |            0         |              0         |               1 |
| T_Amp            | count               |           12 |        36 |           12 |               0         |            0         |              0         |               1 |
| T_Dur            | count               |            1 |         3 |            1 |               0         |            0         |              0         |               1 |
| T_DurFull        | count               |           12 |        36 |           12 |               0         |            0         |              0         |               1 |

## Largest Individual Feature Differences

| feature                 | base_feature     | location   | summary_statistic   |   n_pairs |   mean_abs_error |   median_abs_error |   max_abs_error | allclose_atol_1e_6   |
|:------------------------|:-----------------|:-----------|:--------------------|----------:|-----------------:|-------------------:|----------------:|:---------------------|
| QT_Int_III              | QT_Int           | III        | mean                |         3 |         216.606  |           210.727  |        326      | False                |
| T_DurFull_III           | T_DurFull        | III        | mean                |         3 |         163.714  |           166.364  |        247.143  | False                |
| QT_Int_aVL              | QT_Int           | aVL        | mean                |         3 |         142.442  |           116.545  |        211.143  | False                |
| T_DurFull_V5            | T_DurFull        | V5         | mean                |         3 |         100.831  |            56.3636 |        212.857  | False                |
| QT_Int_aVF              | QT_Int           | aVF        | mean                |         3 |          96.8571 |           104.909  |        160.571  | False                |
| T_DurFull_aVF           | T_DurFull        | aVF        | mean                |         3 |          92.7706 |            86.9091 |        126.857  | False                |
| T_DurFull_V6            | T_DurFull        | V6         | mean                |         3 |          90.9697 |            76.5455 |        148      | False                |
| T_DurFull_V3            | T_DurFull        | V3         | mean                |         3 |          87.4113 |            86      |        123.143  | False                |
| T_DurFull_aVF_iqr       | T_DurFull        | aVF        | iqr                 |         3 |          87.3333 |            62      |        187      | False                |
| T_DurFull_V4            | T_DurFull        | V4         | mean                |         3 |          79.8009 |            55.6364 |        128.857  | False                |
| T_DurFull_aVL           | T_DurFull        | aVL        | mean                |         3 |          77.342  |            77.2727 |        126.571  | False                |
| T_DurFull_V1            | T_DurFull        | V1         | mean                |         3 |          76.4416 |            78.1818 |        102      | False                |
| T_DurFull_V4_iqr        | T_DurFull        | V4         | iqr                 |         3 |          75      |            96      |        127      | False                |
| T_DurFull_V2            | T_DurFull        | V2         | mean                |         3 |          71.5844 |            57.8182 |        132.571  | False                |
| QT_Int_Global           | QT_Int           | Global     | mean                |         3 |          67.7922 |            82.9091 |         94.1818 | False                |
| QT_IntFramingham_Global | QT_IntFramingham | Global     | mean                |         3 |          67.7282 |            86.8731 |        103.322  | False                |
| QT_Int_V5               | QT_Int           | V5         | mean                |         3 |          63.8701 |            91.4286 |         95.0909 | False                |
| T_DurFull_V2_iqr        | T_DurFull        | V2         | iqr                 |         3 |          63.6667 |            50      |         97      | False                |
| QT_Int_I                | QT_Int           | I          | mean                |         3 |          63.4026 |            47.6364 |        104      | False                |
| QT_Int_V4_iqr           | QT_Int           | V4         | iqr                 |         3 |          63.3333 |            78      |        112      | False                |

## Interpretation

- Count columns are much closer than value columns, suggesting beat counts often align while interval/amplitude definitions or aggregation differ.
- T-duration and QT-related direct features show the largest discrepancies in the small PTB-XL audit sample.
- Feature names alone are insufficient for exact PTB-XL+ reproduction.
- Multimodal external validation remains blocked.

## Next Step

Prioritize exact reconstruction of ECGdeli preprocessing, fiducial definitions, summary statistics, and T/QT interval definitions before attempting to fill the remaining external 531-column schema.
