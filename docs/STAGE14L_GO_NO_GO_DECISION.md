# Stage 14L GO/NO-GO Decision

Date: 2026-06-30

Decision: **NO-GO**

## Internal Reduced-Schema Result

| model                         |    auroc |   average_precision |       f1 |
|:------------------------------|---------:|--------------------:|---------:|
| stage14l_signal_embedding_mlp | 0.909411 |            0.7722   | 0.698087 |
| stage14l_structured_mlp       | 0.570364 |            0.304456 | 0        |
| stage14l_fair_concat_mlp      | 0.909666 |            0.7731   | 0.693821 |

## Internal Paired Bootstrap

| comparison                                                   | split   | metric            | left_model                    | right_model              |   left_value |   right_value |   delta_right_minus_left |   paired_bootstrap_ci_lower |   paired_bootstrap_ci_upper | ci_contains_zero   |   n_bootstrap |
|:-------------------------------------------------------------|:--------|:------------------|:------------------------------|:-------------------------|-------------:|--------------:|-------------------------:|----------------------------:|----------------------------:|:-------------------|--------------:|
| stage14l_fair_concat_mlp_minus_stage14l_signal_embedding_mlp | test    | auroc             | stage14l_signal_embedding_mlp | stage14l_fair_concat_mlp |     0.909411 |      0.909666 |              0.000254708 |                -0.000862044 |                  0.00133669 | True               |          1000 |
| stage14l_fair_concat_mlp_minus_stage14l_signal_embedding_mlp | test    | average_precision | stage14l_signal_embedding_mlp | stage14l_fair_concat_mlp |     0.7722   |      0.7731   |              0.000899333 |                -0.00172094  |                  0.00334157 | True               |          1000 |
| stage14l_fair_concat_mlp_minus_stage14l_signal_embedding_mlp | test    | f1                | stage14l_signal_embedding_mlp | stage14l_fair_concat_mlp |     0.698087 |      0.693821 |             -0.00426558  |                -0.0102544   |                  0.00184995 | True               |          1000 |
| stage14l_fair_concat_mlp_minus_stage14l_structured_mlp       | test    | auroc             | stage14l_structured_mlp       | stage14l_fair_concat_mlp |     0.570364 |      0.909666 |              0.339302    |                 0.3231      |                  0.35628    | False              |          1000 |
| stage14l_fair_concat_mlp_minus_stage14l_structured_mlp       | test    | average_precision | stage14l_structured_mlp       | stage14l_fair_concat_mlp |     0.304456 |      0.7731   |              0.468644    |                 0.446545    |                  0.489856   | False              |          1000 |
| stage14l_fair_concat_mlp_minus_stage14l_structured_mlp       | test    | f1                | stage14l_structured_mlp       | stage14l_fair_concat_mlp |     0        |      0.693821 |              0.693821    |                 0.674972    |                  0.711045   | False              |          1000 |

## External Quality Gate

| dataset   | model                    | evaluation_status                     |   n_signal_prediction_records |   n_candidate_structured_records |   n_joinable_signal_structured_records |   record_coverage_fraction |   n_required_reduced_features |   n_available_reduced_features |   structured_missing_fraction |   macro_auroc |   macro_average_precision |   macro_f1 |   signal_only_macro_auroc |   signal_only_macro_average_precision |   signal_only_macro_f1 | blocking_issue                                                             |
|:----------|:-------------------------|:--------------------------------------|------------------------------:|---------------------------------:|---------------------------------------:|---------------------------:|------------------------------:|-------------------------------:|------------------------------:|--------------:|--------------------------:|-----------:|--------------------------:|--------------------------------------:|-----------------------:|:---------------------------------------------------------------------------|
| cpsc2018  | stage14l_fair_concat_mlp | not_evaluated_external_coverage_no_go |                          9944 |                                2 |                                      2 |                0.000201126 |                           138 |                            138 |                             0 |           nan |                       nan |        nan |                  0.907082 |                              0.650903 |               0.590366 | external_reduced_structured_feature_coverage_too_low_or_embeddings_missing |
| chapman   | stage14l_fair_concat_mlp | not_evaluated_external_coverage_no_go |                         45150 |                                2 |                                      2 |                4.42968e-05 |                           138 |                            138 |                             0 |           nan |                       nan |        nan |                  0.874167 |                              0.172664 |               0.164973 | external_reduced_structured_feature_coverage_too_low_or_embeddings_missing |

## Rationale

- internal gain gate: False (min_auroc_gain=0.000255; min_ap_gain=0.000899; auroc_ci_lower_all_positive=False)
- external generation quality gate: False

## Interpretation

If NO-GO, manuscript framing should remain internal multimodal evaluation plus signal-only external validation. Stage 14L does not authorize external multimodal claims.

## Forbidden Claims

- exact PTB-XL+ reproduction
- full 531-column external multimodal validation
- gated fusion superiority
