# BMC MIDM Stage 27 Robustness Revision Log

## Output
- Revised Word manuscript: `manuscript/ECG_PTBXL_BMC_MIDM_SUBMISSION_DRAFT_STAGE27_ROBUSTNESS_REVISED.docx`
- Robustness audit summary: `docs/STAGE27_ROBUSTNESS_AUDIT.md`
- Supplementary tables copied as S11-S13 under `manuscript/tables/`.

## Key robustness findings
- Tolerance sensitivity: 138 features at 1e-6; 138 at 1e-3; 141 at 1e-2.
- Concordance-138 matched concat did not improve over the signal-embedding comparator.
- Random-138 and internally importance-ranked 138 controls recovered internal multimodal gains.
- External candidate structured records remained 2 per dataset; no external multimodal claim was added.

## Manuscript interpretation change
The manuscript now frames Stage 14L/27 as showing information loss in the numerically concordant subset, not as proof that a 138-feature representation is inherently inadequate.

## Default-threshold internal control table

| subset_name                 | model                                                  |    auroc |   average_precision |       f1 |
|:----------------------------|:-------------------------------------------------------|---------:|--------------------:|---------:|
| concordance_138             | stage27_concordance_138_structured_mlp                 | 0.570364 |            0.304456 | 0        |
| concordance_138             | stage27_concordance_138_matched_concat_mlp             | 0.909666 |            0.7731   | 0.693821 |
| random_138_seed2026         | stage27_random_138_seed2026_structured_mlp             | 0.869388 |            0.70438  | 0.623481 |
| random_138_seed2026         | stage27_random_138_seed2026_matched_concat_mlp         | 0.919522 |            0.796006 | 0.711007 |
| importance_138_internal_xai | stage27_importance_138_internal_xai_structured_mlp     | 0.908452 |            0.775284 | 0.698246 |
| importance_138_internal_xai | stage27_importance_138_internal_xai_matched_concat_mlp | 0.922081 |            0.80305  | 0.730975 |

## Bootstrap note
Stage 27 paired bootstrap intervals use 300 record-level resamples as a lightweight screening audit; this is labelled in the summary and should not be confused with the primary manuscript bootstrap analyses.
