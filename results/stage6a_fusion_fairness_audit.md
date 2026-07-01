# Stage 6A Fusion Fairness Audit

## 1. Existing Stage 5 Concat Fusion

- signal input type: frozen signal-model sigmoid probabilities
- signal input dimension: 5
- structured input dimension: 531
- classifier type: logistic regression head
- signal checkpoint used: `results/internal/signal_resnet.pt`
- validation AUROC: 0.899237
- test AUROC: 0.892704

## 2. Methodological Concern

The Stage 5 concat fusion baseline used only five signal probability features together with 531 structured PTB-XL+ features. This gives the structured modality a much richer input representation than the signal modality. If a future gated fusion model uses high-dimensional signal embeddings, the Stage 5 concat fusion result would not be a fair comparator because the input interface and classifier capacity would differ at the same time as the fusion mechanism.

## 3. Required Fix

Both fair MLP-concat and future gated fusion must use the same signal embedding extracted from the strong signal-only encoder, the same leakage-safe structured feature matrix, the same preprocessing rules, the same official PTB-XL split, and the same evaluator. The only intended difference should be the fusion mechanism.

## 4. Status

The old concat fusion should be renamed as:

```text
late-probability concat baseline
```

It should not be used as the main comparator for gated fusion.
