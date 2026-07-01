# Stage 13B Signal-Only External Validation Summary

Date: 2026-06-29

## Scope

This stage evaluates the frozen PTB-XL-trained `strong_signal_only` model on external datasets. No external training, fine-tuning, threshold tuning, or model selection was performed.

Full multimodal external validation was not run because PTB-XL+ compatible structured features are not available for the external datasets.

## Label Scope

| dataset   | main_labels   |   n_records | positive_counts          |
|:----------|:--------------|------------:|:-------------------------|
| cpsc2018  | NORM/CD       |       10330 | NORM=922; CD=2998        |
| chapman   | MI/CD/HYP     |       45151 | MI=123; CD=3058; HYP=751 |

CPSC2018 uses the high-confidence NORM/CD subset. Chapman-Shaoxing uses the high-confidence MI/CD/HYP subset; sinus rhythm is not treated as main-analysis NORM.

## Readable Records

| dataset | indexed records | evaluated records | skipped records |
|---|---:|---:|---:|
| cpsc2018 | 10330 | 9944 | 386 |
| chapman | 45151 | 45150 | 1 |

Skipped records were excluded because WFDB waveform reading failed for those files. No external labels or predictions were imputed.

## Macro Metrics

| dataset   |    auroc |   average_precision |       f1 |   positive_count |   n_records |
|:----------|---------:|--------------------:|---------:|-----------------:|------------:|
| cpsc2018  | 0.907082 |            0.650903 | 0.590366 |             3776 |        9944 |
| chapman   | 0.874167 |            0.172664 | 0.164973 |             3932 |       45150 |

## Interpretation Boundary

- These are signal-only external results, not multimodal external validation.
- These results do not establish clinical readiness.
- Dataset label spaces are only partially aligned with the PTB-XL five-superclass task.

## Next Step

Use these results as conservative signal-only external evidence, or extract PTB-XL+ compatible structured features before any multimodal external validation.
