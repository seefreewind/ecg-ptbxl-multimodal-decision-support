# Stage 8 Ablation Summary

Generated date: 2026-06-28

## 1. Stage Status

Stage 8 completed.

This stage evaluated fair-interface ablations using the same Stage 6A dataset, preprocessing, official split, validation-only early stopping, validation-only threshold tuning, and evaluator.

No XAI, uncertainty analysis, DCA, external validation, or manuscript writing was performed.

## 2. Ablation Models

- strong signal-only: original strong waveform model reference
- signal-embedding MLP: 256-dimensional strong signal embedding only
- structured MLP: 531 leakage-safe PTB-XL+ features only
- fair MLP-concat: 256 signal embedding + 531 structured features
- gated fusion MLP: same inputs with learned gate

## 3. Single-Seed Test Results

| model | test AUROC | test average precision | test F1 |
|---|---:|---:|---:|
| strong signal-only | 0.909815 | 0.772057 | 0.699812 |
| signal-embedding MLP | 0.909437 | 0.772363 | 0.700216 |
| structured MLP | 0.904558 | 0.765152 | 0.689893 |
| fair MLP-concat | 0.919251 | 0.795289 | 0.720762 |
| gated fusion MLP | 0.919570 | 0.797779 | 0.725463 |

## 4. Repeated Seeds

- signal-embedding MLP test AUROC mean / SD: 0.909261 / 0.000282
- signal-embedding MLP test F1 mean / SD: 0.699800 / 0.002070
- structured MLP test AUROC mean / SD: 0.905795 / 0.001084
- structured MLP test F1 mean / SD: 0.689196 / 0.001283

## 5. Interpretation

The ablation confirms that the fair fusion models are compared against both unimodal fair-interface baselines. Gated fusion remains slightly above fair MLP-concat in the single-seed frozen test result, but the margin is small and should be interpreted cautiously until later calibration, uncertainty, and external validation are completed.

## 6. Next Step

Proceed to calibration under the same frozen validation/test protocol. Do not start manuscript result writing yet.
