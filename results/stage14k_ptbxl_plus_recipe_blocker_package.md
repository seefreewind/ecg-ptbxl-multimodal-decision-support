# Stage 14K PTB-XL+ Recipe Blocker Package

Date: 2026-06-30

## Purpose

This package defines the exact blocker for external multimodal validation. It separates validated progress from unresolved PTB-XL+ feature-reconstruction requirements.

It does not generate structured feature tables, does not run multimodal external validation, and does not change the external schema gate.

## Decision

| can_claim_exact_ptbxl_plus_reproduction   | can_run_multimodal_external_validation   |   n_blocked_requirements | blocking_issue                                                         | allowed_next_step                                                                      |
|:------------------------------------------|:-----------------------------------------|-------------------------:|:-----------------------------------------------------------------------|:---------------------------------------------------------------------------------------|
| False                                     | False                                    |                        6 | direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing | obtain_or_reconstruct_exact_ptbxl_plus_recipe_then_rerun_schema_and_numeric_validation |

## Unlock Requirements

| requirement                                                             | current_evidence                                                                                                                                                  | minimum_unlock_condition                                                                                                                                                               | status   |
|:------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| Complete exact 531-column PTB-XL+ waveform-to-feature recipe            | Stage 14F maps 420 direct candidates but leaves 39 unknown-recipe columns plus formula/morphology columns.                                                        | All 531 frozen structured columns can be generated from external waveforms with documented formulas, units, lead handling, summary statistics, and missing-value rules.                | blocked  |
| Numeric agreement with official PTB-XL+ for direct ECGdeli candidates   | Stage 14H allclose direct features: 138/420; median feature MAE 0.059102.                                                                                         | A held-out PTB-XL recomputation audit shows near-exact agreement for direct features under a prespecified tolerance.                                                                   | blocked  |
| Resolve T/QT interval discrepancy mechanism                             | Stage 14I worst family is T_DurFull:mean; 32 families show at least one discrepancy.                                                                              | Preprocessing, fiducial selection, beat inclusion, interval definition, and aggregation choices explain and remove the mismatch.                                                       | blocked  |
| Implement QT_IntCorr, P_Morph, ST_Elev, and HA__Global rules            | Stage 14J finds semantic descriptions for 111/111 unresolved columns, but not an executable recipe.                                                               | Each unresolved family has executable code and numeric validation against official PTB-XL+ examples.                                                                                   | blocked  |
| Generate nonempty external 531-column structured feature tables         | Stage 14C schema gate still reports missing official external structured tables; Stage 14G candidate files intentionally contain only 420 direct feature columns. | data/processed/external/cpsc2018_structured_features.csv and data/processed/external/chapman_structured_features.csv exist, are nonempty, and exactly match the frozen PTB-XL+ schema. | blocked  |
| Keep candidate/prototype files separate from official multimodal inputs | Stage 14E prototype and Stage 14G direct-candidate files are useful engineering evidence but are incomplete.                                                      | Only exact 531-column validated files are registered as external structured features; prototype/candidate files remain excluded.                                                       | blocked  |

## Current Evidence

- MATLAB R2025a and official ECGdeli are callable, and the ECGdeli smoke test passes.
- External WFDB records from CPSC2018 and Chapman-Shaoxing can enter the ECGdeli extraction path.
- A 420-column direct candidate generator works technically, but its PTB-XL recomputation does not numerically match official PTB-XL+ values closely enough.
- The remaining 111 frozen PTB-XL+ columns have semantic descriptions, but semantic descriptions are not a full executable recipe.

## Practical Consequence

Only signal-only external validation is currently supportable. Fair concat or gated multimodal external validation must wait until exact 531-column external structured tables pass both schema validation and numeric sanity checks.

## Minimum Evidence Needed To Proceed

1. Exact PTB-XL+ feature-generation code or a faithful reconstruction of it.
2. A PTB-XL internal recomputation audit showing numeric agreement with official PTB-XL+ feature values.
3. Nonempty CPSC2018 and Chapman-Shaoxing external structured feature tables with the frozen 531-column schema.
4. A passing Stage 14C schema gate before any external fair concat or gated fusion evaluation.
