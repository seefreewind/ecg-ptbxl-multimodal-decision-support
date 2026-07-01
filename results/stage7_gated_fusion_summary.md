# Stage 7 Gated Fusion Baseline Summary

Generated date: 2026-06-28

## 1. Stage Status

Stage 7 completed.

This stage implemented a gated fusion baseline using the same fair fusion interface established in Stage 6A. It did not change the signal embeddings, structured feature matrix, preprocessing, official split, validation-only early stopping, validation-only threshold tuning, or evaluator.

No XAI, uncertainty analysis, DCA, external validation, or manuscript writing was performed in this stage.

## 2. Fair Interface

- signal input: strong SignalResNet pooled embedding
- signal embedding dim: 256
- structured input: leakage-safe PTB-XL+ `ecgdeli_features.csv` features
- structured feature dim: 531
- preprocessing: Stage 6A train-only preprocessing artifact
- official split preserved: yes
- test role: frozen_final_evaluation_only

## 3. Gated Fusion Mechanism

The model projects signal and structured inputs into a shared hidden representation and learns a sigmoid gate:

```text
fused = gate * signal_hidden + (1 - gate) * structured_hidden
```

This is a gated-fusion baseline, not an interpretability or XAI analysis.

## 4. Single-Seed Results

| split | threshold mode | AUROC | average precision | F1 |
|---|---|---:|---:|---:|
| validation | default 0.5 | 0.923115 | 0.798390 | 0.727885 |
| validation | validation tuned | 0.923115 | 0.798390 | 0.742329 |
| test | default 0.5 | 0.919570 | 0.797779 | 0.725463 |
| test | validation tuned | 0.919570 | 0.797779 | 0.729345 |

## 5. Repeated Seeds and Bootstrap

- seeds: 2026, 2027, 2028
- test AUROC mean / SD: 0.919883 / 0.000478
- test F1 mean / SD: 0.717497 / 0.007107
- test AUROC bootstrap CI: 0.919570 [0.911781, 0.926943]
- test F1 bootstrap CI: 0.725463 [0.708431, 0.743010]

## 6. Gate Diagnostics

| split | gate mean | gate SD | gate min | gate max |
|---|---:|---:|---:|---:|
| validation | 0.697149 | 0.251852 | 0.000000 | 1.000000 |
| test | 0.696180 | 0.250718 | 0.000003 | 1.000000 |

## 7. Comparison

See:

```text
tables/table_stage7_gated_fusion_comparison.csv
```

Key frozen test AUROC values:

| model | test macro AUROC |
|---|---:|
| strong signal-only | 0.909815 |
| structured-only | 0.874455 |
| late-probability concat | 0.892704 |
| fair MLP-concat | 0.919251 |
| gated fusion MLP | 0.919570 |

Gated fusion exceeds fair MLP-concat on frozen test macro AUROC: yes (0.919570 vs 0.919251).

Gated fusion exceeds strong signal-only on frozen test macro AUROC: yes (0.919570 vs 0.909815).

## 8. Readiness Decision

Ready for ablation if the next stage preserves this same fair interface.

The gated fusion baseline is now implemented and evaluated, but this is still internal PTB-XL validation/test evidence only. It is not external validation and should not be written as a clinically validated decision-support framework.

## 9. Next Step

Proceed to ablation under the same interface:

```text
signal-only embedding MLP
structured-only MLP
fair MLP-concat
gated fusion MLP
```

Then calibration, uncertainty, XAI, and external validation can be considered in later stages.
