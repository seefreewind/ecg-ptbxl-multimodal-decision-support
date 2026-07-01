# Revised Multimodal Story and Contribution Positioning

Generated date: 2026-06-28

## Core Empirical Finding

The current fair-interface experiments do not support a claim that gated fusion is meaningfully superior to simple fair MLP-concat.

Frozen test results:

| model | test AUROC | test AP | test F1 |
|---|---:|---:|---:|
| fair MLP-concat | 0.919251 | 0.795289 | 0.720762 |
| gated fusion MLP | 0.919570 | 0.797779 | 0.725463 |
| delta | +0.000319 | +0.002489 | +0.004702 |

The AUROC difference is very small and falls within the observed repeated-seed variability. Therefore, the manuscript should not use "gated fusion improves over concat" as the central claim.

## Revised Main Claim

The supported claim is:

```text
ECG signal embeddings and structured ECG features provide complementary information for PTB-XL cardiac risk stratification. Under a strict fair-interface evaluation, multimodal fusion improves over either unimodal baseline, while simple MLP-concat captures most of the gain and gated fusion adds no clear discrimination advantage.
```

## Revised Contributions

1. Strict fair multimodal evaluation framework:
   unified signal embedding, unified structured feature matrix, official PTB-XL split, validation-only model selection/threshold tuning, frozen test evaluation, and comparable classifier heads.

2. Systematic multimodal complementarity ablation:
   signal-embedding MLP, structured MLP, fair MLP-concat, and gated fusion are compared under the same interface. The results show that multimodal gains come from modality complementarity rather than fusion-mechanism complexity.

3. Trustworthy decision-support analysis:
   calibration, uncertainty analysis, XAI, DCA, and external validation should carry the decision-support contribution. These analyses must remain conservative and should not claim clinical readiness without independent validation.

## How to Report the Gated Result

Use cautious wording:

```text
Gated fusion produced a numerically similar test AUROC to fair MLP-concat, and the observed difference was small. This suggests that a simple fair concat interface may be sufficient for capturing most of the multimodal gain in this internal PTB-XL setting.
```

Avoid:

```text
Gated fusion substantially outperformed concat fusion.
```

## Next Experiments

1. Calibration and reliability analysis across all main models.
2. Paired bootstrap test for gated fusion versus fair MLP-concat.
3. Uncertainty and confidence-based triage.
4. Dual-modality XAI.
5. Decision curve analysis.
6. External validation.
