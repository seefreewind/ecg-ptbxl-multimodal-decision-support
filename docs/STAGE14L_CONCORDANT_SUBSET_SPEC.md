# Stage 14L Concordant-Subset External Multimodal Validation Spec

Date: 2026-06-30

## Scope

Stage 14L uses only structured features that passed Stage 14H PTB-XL internal ECGdeli recomputation allclose checks. It intentionally does not attempt full PTB-XL+ 531-column reproduction.

## Reduced Structured Schema

- feature count: 138
- source: Stage 14H allclose direct ECGdeli candidate features
- excluded: all non-allclose direct candidates and all unresolved QT_IntCorr/P_Morph/ST_Elev/HA features

## Internal Protocol

- train/val/test split: unchanged PTB-XL official split
- label scope: NORM, MI, STTC, CD, HYP
- comparators: signal-embedding MLP, reduced structured MLP, reduced fair concat MLP
- model selection and threshold tuning: validation only
- test set: frozen final evaluation only

## External Protocol

External multimodal evaluation is allowed only if reduced structured features and signal embeddings are available for a sufficient fraction of CPSC2018 and Chapman-Shaoxing records. Candidate/prototype features are not treated as exact PTB-XL+ reproduction.

## Forbidden Claims

- exact PTB-XL+ reproduction
- full 531-column external multimodal validation
- gated fusion superiority
