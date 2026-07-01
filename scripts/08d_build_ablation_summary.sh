#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" - <<'PY'
import json
from pathlib import Path
import pandas as pd

tables = {
    "strong signal-only": "tables/table_signal_strong_baseline_results.csv",
    "signal-embedding MLP": "tables/table_signal_embedding_mlp_results.csv",
    "structured MLP": "tables/table_structured_mlp_results.csv",
    "fair MLP-concat": "tables/table_fair_concat_results.csv",
    "gated fusion MLP": "tables/table_gated_fusion_results.csv",
}
rows = []
for name, path in tables.items():
    df = pd.read_csv(path)
    if "threshold_mode" in df.columns:
        df = df[df["threshold_mode"].eq("default_0.5")]
    test = df[df["split"].eq("test")].iloc[0]
    val = df[df["split"].eq("val")].iloc[0]
    rows.append(
        {
            "model": name,
            "validation_macro_auroc": float(val["auroc"]),
            "test_macro_auroc": float(test["auroc"]),
            "test_macro_average_precision": float(test["average_precision"]),
            "test_macro_f1": float(test["f1"]),
        }
    )
comparison = pd.DataFrame(rows)
comparison.to_csv("tables/table_stage8_ablation_comparison.csv", index=False)
rep = pd.read_csv("tables/table_ablation_repeated_seed_summary.csv")
sig_rep = rep[(rep["ablation_model"].eq("signal_embedding_mlp")) & (rep["split"].eq("test"))].iloc[0]
struct_rep = rep[(rep["ablation_model"].eq("structured_mlp")) & (rep["split"].eq("test"))].iloc[0]

text = f"""# Stage 8 Ablation Summary

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
"""
for row in rows:
    text += f"| {row['model']} | {row['test_macro_auroc']:.6f} | {row['test_macro_average_precision']:.6f} | {row['test_macro_f1']:.6f} |\n"
text += f"""
## 4. Repeated Seeds

- signal-embedding MLP test AUROC mean / SD: {sig_rep['auroc_mean']:.6f} / {sig_rep['auroc_std']:.6f}
- signal-embedding MLP test F1 mean / SD: {sig_rep['f1_mean']:.6f} / {sig_rep['f1_std']:.6f}
- structured MLP test AUROC mean / SD: {struct_rep['auroc_mean']:.6f} / {struct_rep['auroc_std']:.6f}
- structured MLP test F1 mean / SD: {struct_rep['f1_mean']:.6f} / {struct_rep['f1_std']:.6f}

## 5. Interpretation

The ablation confirms that the fair fusion models are compared against both unimodal fair-interface baselines. Gated fusion remains slightly above fair MLP-concat in the single-seed frozen test result, but the margin is small and should be interpreted cautiously until later calibration, uncertainty, and external validation are completed.

## 6. Next Step

Proceed to calibration under the same frozen validation/test protocol. Do not start manuscript result writing yet.
"""
Path("results/stage8_ablation_summary.md").write_text(text, encoding="utf-8")
print(comparison.to_string(index=False))
PY
