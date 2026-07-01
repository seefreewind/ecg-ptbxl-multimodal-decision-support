# Stage 27 Robustness Audit

## Scope

This stage is an internal robustness and engineering-feasibility audit. It does not add external multimodal validation and does not revise the locked signal-only external evidence boundary. Paired bootstrap intervals in this screening audit use 300 record-level resamples to keep the analysis lightweight; confirmatory manuscript CIs can be rerun with more resamples if needed.

## Tolerance Sensitivity

|    atol |    rtol |   n_features_passing |   fraction_of_direct_candidates |   n_direct_candidates_evaluated |
|--------:|--------:|---------------------:|--------------------------------:|--------------------------------:|
|  1e-06  |  1e-06  |                  138 |                        0.328571 |                             420 |
|  0.0001 |  0.0001 |                  138 |                        0.328571 |                             420 |
|  0.001  |  0.001  |                  138 |                        0.328571 |                             420 |
|  0.01   |  0.01   |                  141 |                        0.335714 |                             420 |
|  0.1    |  0.1    |                  238 |                        0.566667 |                             420 |
|  1      |  1      |                  389 |                        0.92619  |                             420 |
|  5      |  5      |                  415 |                        0.988095 |                             420 |
| 10      | 10      |                  419 |                        0.997619 |                             420 |

Interpretation: the tolerance check is exact for the available PTB-XL recomputation audit sample, but the sample contains only three recomputed records. It should be used as a sensitivity audit, not as a definitive feature-recipe validation.

## Feature-Count Controls

| subset_name                 | model                                                  |    auroc |   average_precision |       f1 |   positive_count |
|:----------------------------|:-------------------------------------------------------|---------:|--------------------:|---------:|-----------------:|
| concordance_138             | stage27_concordance_138_structured_mlp                 | 0.570364 |            0.304456 | 0        |             2792 |
| concordance_138             | stage27_concordance_138_matched_concat_mlp             | 0.909666 |            0.7731   | 0.693821 |             2792 |
| random_138_seed2026         | stage27_random_138_seed2026_structured_mlp             | 0.869388 |            0.70438  | 0.623481 |             2792 |
| random_138_seed2026         | stage27_random_138_seed2026_matched_concat_mlp         | 0.919522 |            0.796006 | 0.711007 |             2792 |
| importance_138_internal_xai | stage27_importance_138_internal_xai_structured_mlp     | 0.908452 |            0.775284 | 0.698246 |             2792 |
| importance_138_internal_xai | stage27_importance_138_internal_xai_matched_concat_mlp | 0.922081 |            0.80305  | 0.730975 |             2792 |

## Paired Bootstrap

| subset_name                 | comparison                                                                                                      | metric            |   left_value |   right_value |   delta_right_minus_left |   paired_bootstrap_ci_lower |   paired_bootstrap_ci_upper | ci_contains_zero   |
|:----------------------------|:----------------------------------------------------------------------------------------------------------------|:------------------|-------------:|--------------:|-------------------------:|----------------------------:|----------------------------:|:-------------------|
| concordance_138             | stage27_concordance_138_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                                  | auroc             |     0.909411 |      0.909666 |              0.000254708 |                -0.000833003 |                  0.00129639 | True               |
| concordance_138             | stage27_concordance_138_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                                  | average_precision |     0.7722   |      0.7731   |              0.000899333 |                -0.00174146  |                  0.00341004 | True               |
| concordance_138             | stage27_concordance_138_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                                  | f1                |     0.698087 |      0.693821 |             -0.00426558  |                -0.0101026   |                  0.00210722 | True               |
| concordance_138             | stage27_concordance_138_matched_concat_mlp_minus_stage27_concordance_138_structured_mlp                         | auroc             |     0.570364 |      0.909666 |              0.339302    |                 0.321933    |                  0.355699   | False              |
| concordance_138             | stage27_concordance_138_matched_concat_mlp_minus_stage27_concordance_138_structured_mlp                         | average_precision |     0.304456 |      0.7731   |              0.468644    |                 0.448403    |                  0.486987   | False              |
| concordance_138             | stage27_concordance_138_matched_concat_mlp_minus_stage27_concordance_138_structured_mlp                         | f1                |     0        |      0.693821 |              0.693821    |                 0.67568     |                  0.709175   | False              |
| random_138_seed2026         | stage27_random_138_seed2026_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                              | auroc             |     0.909411 |      0.919522 |              0.0101115   |                 0.00747601  |                  0.0127991  | False              |
| random_138_seed2026         | stage27_random_138_seed2026_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                              | average_precision |     0.7722   |      0.796006 |              0.0238052   |                 0.0172887   |                  0.0303049  | False              |
| random_138_seed2026         | stage27_random_138_seed2026_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                              | f1                |     0.698087 |      0.711007 |              0.0129202   |                 0.00254568  |                  0.0239158  | False              |
| random_138_seed2026         | stage27_random_138_seed2026_matched_concat_mlp_minus_stage27_random_138_seed2026_structured_mlp                 | auroc             |     0.869388 |      0.919522 |              0.0501344   |                 0.0432105   |                  0.0587598  | False              |
| random_138_seed2026         | stage27_random_138_seed2026_matched_concat_mlp_minus_stage27_random_138_seed2026_structured_mlp                 | average_precision |     0.70438  |      0.796006 |              0.0916256   |                 0.0768523   |                  0.108388   | False              |
| random_138_seed2026         | stage27_random_138_seed2026_matched_concat_mlp_minus_stage27_random_138_seed2026_structured_mlp                 | f1                |     0.623481 |      0.711007 |              0.0875264   |                 0.0683344   |                  0.106009   | False              |
| importance_138_internal_xai | stage27_importance_138_internal_xai_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                      | auroc             |     0.909411 |      0.922081 |              0.0126705   |                 0.00925867  |                  0.016109   | False              |
| importance_138_internal_xai | stage27_importance_138_internal_xai_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                      | average_precision |     0.7722   |      0.80305  |              0.0308497   |                 0.0209714   |                  0.0403097  | False              |
| importance_138_internal_xai | stage27_importance_138_internal_xai_matched_concat_mlp_minus_stage14l_signal_embedding_mlp                      | f1                |     0.698087 |      0.730975 |              0.0328888   |                 0.0203476   |                  0.0459341  | False              |
| importance_138_internal_xai | stage27_importance_138_internal_xai_matched_concat_mlp_minus_stage27_importance_138_internal_xai_structured_mlp | auroc             |     0.908452 |      0.922081 |              0.0136293   |                 0.00862274  |                  0.0193083  | False              |
| importance_138_internal_xai | stage27_importance_138_internal_xai_matched_concat_mlp_minus_stage27_importance_138_internal_xai_structured_mlp | average_precision |     0.775284 |      0.80305  |              0.0277658   |                 0.0140924   |                  0.0427977  | False              |
| importance_138_internal_xai | stage27_importance_138_internal_xai_matched_concat_mlp_minus_stage27_importance_138_internal_xai_structured_mlp | f1                |     0.698246 |      0.730975 |              0.0327294   |                 0.0187775   |                  0.0473855  | False              |

## External Join Failure Audit

| dataset   |   n_signal_prediction_records |   n_candidate_feature_records |   n_joinable_records |   join_coverage |   n_required_reduced_features |   n_available_reduced_features |   n_missing_reduced_features |   feature_schema_coverage | dominant_failure_mode                                                         | interpretation                                                                                                    |
|:----------|------------------------------:|------------------------------:|---------------------:|----------------:|------------------------------:|-------------------------------:|-----------------------------:|--------------------------:|:------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------|
| cpsc2018  |                          9944 |                             2 |                    2 |     0.000201126 |                           138 |                            138 |                            0 |                         1 | candidate_feature_record_count_and_external_signal_embedding_coverage_too_low | Engineering feasibility audit only; not evidence that external PTB-XL+ reconstruction is impossible in principle. |
| chapman   |                         45150 |                             2 |                    2 |     4.42968e-05 |                           138 |                            138 |                            0 |                         1 | candidate_feature_record_count_and_external_signal_embedding_coverage_too_low | Engineering feasibility audit only; not evidence that external PTB-XL+ reconstruction is impossible in principle. |

## Manuscript Implication

If random-138 or importance-138 controls recover internal multimodal gain, the manuscript should say that the concordant subset loses information and therefore cannot support external multimodal validation; it should not imply that every 138-feature subset fails. If no 138-feature control recovers gain, the current dimensionality-loss explanation becomes less likely, but the result remains internal only.
