# Stage 14J PTB-XL+ Feature Description Audit Summary

Date: 2026-06-30

## Status

The official PTB-XL+ feature description table was audited against the 111 frozen structured feature columns that remain outside the direct ECGdeli candidate set.

This stage is documentation and recipe triage only. It does not generate external structured feature tables and does not unlock multimodal external validation.

## Decision

| can_generate_exact_531_features   | can_run_multimodal_external_validation   |   unresolved_feature_columns |   unresolved_columns_with_feature_description |   unresolved_columns_without_feature_description | blocking_issue                                                         | notes                                                                                                                                                                                                                                                       |
|:----------------------------------|:-----------------------------------------|-----------------------------:|----------------------------------------------:|-------------------------------------------------:|:-----------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| False                             | False                                    |                          111 |                                           111 |                                                0 | direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing | feature_description.csv provides useful semantics for unresolved PTB-XL+ features, but it does not resolve the exact aggregation recipe and does not explain the observed numeric mismatch between local ECGdeli recomputation and official PTB-XL+ values. |

## Unresolved Feature Families

| base_feature   | derivability                 | description_found   |   n_features | example_description_id   | example_ecgdeli_feature   | example_description                                                                                                                                                                                                 |
|:---------------|:-----------------------------|:--------------------|-------------:|:-------------------------|:--------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| HA_            | unknown_recipe               | True                |            3 | HA__Global               | elHA                      | electrical heart axis (1: left axis deviation, 2: horizontal axis, 3: normal axis, 4: vertical axis, 5: right axis, 6: extreme right axis deviation)                                                                |
| P_Morph        | requires_morphology_function | True                |           36 | P_Morph_X                | PWm_X                     | P wave morphology in lead X (-3: negative m-shaped, -2: negative biphasic, -1: negative monophasic, 1: positive monophasic, 2: positive biphasic, 3: positive m-shaped for KIT, Glasgow & GE only between -2 and 2) |
| QT_IntCorr     | requires_extra_formula       | True                |           36 | QT_IntCorr_X             | QTci_X                    | Q-T interval corrected based on Framingham formula in lead X                                                                                                                                                        |
| ST_Elev        | unknown_recipe               | True                |           36 | ST_Elev_X                | STc_X                     | ST elevation/depression from multiple Gaussian fits in lead X                                                                                                                                                       |

## Documented But Still Not Reproducible

| base_feature   |   n_features | example_description_id   | example_ecgdeli_feature   | example_description                                                                                                                                                                                                 |
|:---------------|-------------:|:-------------------------|:--------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| HA_            |            3 | HA__Global               | elHA                      | electrical heart axis (1: left axis deviation, 2: horizontal axis, 3: normal axis, 4: vertical axis, 5: right axis, 6: extreme right axis deviation)                                                                |
| P_Morph        |           36 | P_Morph_X                | PWm_X                     | P wave morphology in lead X (-3: negative m-shaped, -2: negative biphasic, -1: negative monophasic, 1: positive monophasic, 2: positive biphasic, 3: positive m-shaped for KIT, Glasgow & GE only between -2 and 2) |
| QT_IntCorr     |           36 | QT_IntCorr_X             | QTci_X                    | Q-T interval corrected based on Framingham formula in lead X                                                                                                                                                        |
| ST_Elev        |           36 | ST_Elev_X                | STc_X                     | ST elevation/depression from multiple Gaussian fits in lead X                                                                                                                                                       |

## Interpretation

- `feature_description.csv` confirms that several unresolved families have official semantic descriptions, including QT correction, P morphology, ST elevation, and electrical heart axis.
- These descriptions identify expected feature concepts or ECGdeli-style names, but they do not define a complete waveform-to-531-column recipe.
- Stage 14H/14I already showed that even the direct 420-feature subset does not numerically match official PTB-XL+ values closely enough to claim exact reproduction.
- Therefore, external multimodal validation remains blocked until an exact PTB-XL+ feature-generation recipe is obtained or reconstructed and validated numerically.

## Next Step

Prepare a compact recipe-blocker package listing the exact missing definitions, numeric mismatch evidence, and the minimum requirements for unlocking external multimodal validation.
