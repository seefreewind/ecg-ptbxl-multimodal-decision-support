# Stage 6A Fair Fusion Summary

## 1. Why Stage 5 Concat Was Not a Fair Gated Comparator

- signal input type: 5 frozen signal probabilities
- signal input dim: 5
- structured input dim: 531
- classifier type: logistic regression head
- reason it is archived as late-probability concat: it uses only five signal probability features rather than the high-dimensional strong signal encoder representation that future gated fusion will receive.

## 2. Strong Signal Embedding Extraction

- checkpoint used: `results/internal/signal_strong/signal_strong_best.pt`
- embedding layer: global pooled representation before final classifier
- embedding dim: 256
- train rows: 17418
- validation rows: 2183
- test rows: 2198

## 3. Fair Fusion Dataset

- structured features: 531
- total feature dim: 787
- preprocessing: train-only median imputation and train-only standardization; validation/test transformed only
- official split preserved: yes

## 4. Fair MLP-Concat Results

- validation macro AUROC: 0.922679
- test macro AUROC: 0.919251
- validation macro F1 default: 0.729732
- validation macro F1 tuned: 0.741111
- test macro F1 default: 0.720762
- test macro F1 tuned: 0.728135

## 5. Repeated Seeds and Bootstrap

- seeds: 2026, 2027, 2028
- test AUROC mean / SD: 0.918941 / 0.000269
- test F1 mean / SD: 0.715398 / 0.008096
- test AUROC bootstrap CI: 0.919251 [0.911797, 0.926395]
- test F1 bootstrap CI: 0.720762 [0.704297, 0.737049]

## 6. Comparison Table

See:

```text
tables/table_fusion_baseline_fairness_comparison.csv
```

Key frozen test AUROC values:

| model | test macro AUROC | fair comparator for gated |
|---|---:|---|
| strong signal-only | 0.909815 | reference |
| structured-only | 0.874455 | reference |
| late-probability concat | 0.892704 | no |
| fair MLP-concat | 0.919251 | yes |

## 7. Readiness Decision

Ready for gated fusion using the same embeddings and MLP head.

Fair MLP-concat exceeds strong signal-only on frozen test macro AUROC: yes (0.919251 vs 0.909815).

Fair MLP-concat exceeds late-probability concat on frozen test macro AUROC: yes (0.919251 vs 0.892704).

Fair MLP-concat is sufficient as the fair gated-fusion comparator because it uses the strong signal embedding, 531 leakage-safe structured features, train-only preprocessing, the official split, and an MLP head.

## 8. Next Step

Implement gated fusion using the same signal embeddings, same structured features, same preprocessing, and comparable MLP head. Do not change the fusion interface while evaluating the gated mechanism.
