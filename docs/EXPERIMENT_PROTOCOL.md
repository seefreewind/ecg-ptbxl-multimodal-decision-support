# Experiment Protocol

## Official PTB-XL Split

Official PTB-XL folds are used.

```text
train: strat_fold 1-8
validation: strat_fold 9
test: strat_fold 10
```

The generated split files are:

```text
data/splits/ptbxl_train.csv
data/splits/ptbxl_val.csv
data/splits/ptbxl_test.csv
```

## Frozen Test Rule

All hyperparameter tuning, threshold tuning, early stopping, and model selection are performed only on the validation split.

The test split is frozen and used only for final reporting.

## Allowed Uses By Split

| split | allowed use |
|---|---|
| train | parameter fitting |
| validation | early stopping, best checkpoint selection, threshold tuning, hyperparameter selection |
| test | final evaluation only |

## Guardrails

- Threshold tuning must use validation predictions only.
- Early stopping must use validation metrics only.
- Best checkpoint selection must use validation metrics only.
- Test metrics are computed only after the best checkpoint has been selected.
- No code should modify model parameters, thresholds, or hyperparameters based on test performance.

## Current Stage Boundary

Stage 2 permits signal-only strong baseline work and PTB-XL+ validation/alignment infrastructure. It does not permit gated fusion, SHAP, Grad-CAM, uncertainty, DCA, external validation conclusions, or manuscript result writing.

