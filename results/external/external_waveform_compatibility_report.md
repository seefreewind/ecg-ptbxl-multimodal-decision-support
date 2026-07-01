# External Waveform Compatibility Report

Generated date: 2026-06-29

| dataset   |   n_records_checked |   lead_count | lead_order_detected                    |   sampling_rate_detected |   duration_detected |   target_sampling_rate |   target_length | requires_resampling   | requires_padding_or_cropping   | compatible_with_signal_model   | blocking_issue   | notes                                      |
|:----------|--------------------:|-------------:|:---------------------------------------|-------------------------:|--------------------:|-----------------------:|----------------:|:----------------------|:-------------------------------|:-------------------------------|:-----------------|:-------------------------------------------|
| cpsc2018  |                  11 |           12 | I,II,III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6 |                      500 |                  14 |                    100 |            1000 | True                  | True                           | True                           |                  | Compatible after documented preprocessing. |
| chapman   |                  10 |           12 | I,II,III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6 |                      500 |                  10 |                    100 |            1000 | True                  | False                          | True                           |                  | Compatible after documented preprocessing. |

Target signal-model input shape: `12 channels x 1000 samples`.
