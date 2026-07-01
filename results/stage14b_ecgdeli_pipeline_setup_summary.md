# Stage 14B ECGdeli / PTB-XL+ Exact Pipeline Setup Summary

Date: 2026-06-30

## Status

The relevant repositories were cloned and audited locally. PyWavelets was installed so the Python ECGdeli port can be imported for exploratory checks. However, an exact waveform-to-PTB-XL+ 531-column feature extraction pipeline is not yet runnable.

## Components

| component                 | path                                                      | available   | commit                                   | role                                                             | exact_ptbxl_plus_feature_generator   | validation_status                    | notes                                                                                                                                                                                                                   |
|:--------------------------|:----------------------------------------------------------|:------------|:-----------------------------------------|:-----------------------------------------------------------------|:-------------------------------------|:-------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ptbxl_feature_benchmark   | tools/external_feature_extractors/ptbxl_feature_benchmark | True        | 4c37b775e56d23e2c844fcd0aec52d2cd05cb35e | official PTB-XL+ benchmark code                                  | False                                | not_exact_generator                  | benchmark consumes downloaded ecgdeli_features.csv; no waveform-to-feature extraction recipe found                                                                                                                      |
| ECGdeli_MATLAB            | tools/external_feature_extractors/ECGdeli                 | True        | c3738612771264e4d6c4686898ef7b2d6a700ad3 | official ECGdeli MATLAB delineation toolbox                      | False                                | matlab_available_needs_schema_recipe | ECGdeli requires MATLAB image/signal/statistics/wavelet toolboxes. MATLAB smoke: 25.1.0.2943329 (R2025a). Toolbox smoke: butter=available; filtfilt=available; fitcsvm=available; imresize=available; wavedec=available |
| pyECGdeli                 | tools/external_feature_extractors/pyECGdeli               | True        | 38d7b762237d004117d9833d32f5326a79451c91 | Python ECGdeli port for exploratory audit only                   | False                                | not_exact_generator                  | import ok; README says work in progress and not a complete PTB-XL+ 531-feature generator.                                                                                                                               |
| MATLAB_runtime            | /Applications/MATLAB_R2025a.app/bin/matlab                | True        |                                          | required runtime for official ECGdeli                            | False                                | licensed                             | 25.1.0.2943329 (R2025a)                                                                                                                                                                                                 |
| MATLAB_required_toolboxes | /Applications/MATLAB_R2025a.app/bin/matlab                | True        |                                          | required MATLAB toolbox functions for ECGdeli feature extraction | False                                | available                            | butter=available; filtfilt=available; fitcsvm=available; imresize=available; wavedec=available                                                                                                                          |
| Octave_runtime            |                                                           | False       |                                          | possible smoke-test runtime only                                 | False                                | missing                              | Octave is not treated as validated replacement for MATLAB ECGdeli plus required toolboxes.                                                                                                                              |
| target_schema             | data/processed/structured_feature_names.txt               | True        |                                          | required frozen structured feature schema                        | False                                | schema_available                     | 531 required PTB-XL+ structured feature names loaded.                                                                                                                                                                   |

## Decision

| can_run_exact_external_feature_extraction   | can_run_full_multimodal_external_validation   | recommended_next_action                                                                                | blocking_issue                                     |
|:--------------------------------------------|:----------------------------------------------|:-------------------------------------------------------------------------------------------------------|:---------------------------------------------------|
| False                                       | False                                         | obtain PTB-XL+ ecgdeli extraction recipe and MATLAB runtime/toolboxes, then validate 531-column schema | ptbxl_plus_exact_feature_generation_recipe_missing |

## Interpretation

- The PTB-XL+ benchmark repository consumes downloaded `ecgdeli_features.csv`; it does not provide the missing waveform-to-feature extraction recipe.
- The configured MATLAB runtime and required toolbox function smoke tests are available.
- pyECGdeli is importable after installing PyWavelets, but it is not a complete or validated PTB-XL+ 531-feature generator.
- Therefore, full multimodal external validation remains blocked.

## Next Step

Obtain a MATLAB runtime with the required toolboxes and the exact PTB-XL+ ECGdeli feature aggregation recipe, or obtain external structured feature tables already matching the 531 frozen PTB-XL+ columns.
