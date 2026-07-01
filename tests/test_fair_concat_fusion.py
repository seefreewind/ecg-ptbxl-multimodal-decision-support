from __future__ import annotations

from pathlib import Path

import pandas as pd
import torch


def test_fusion_mlp_outputs_multilabel_logits() -> None:
    from src.models.fusion_mlp import FusionMLP

    model = FusionMLP(input_dim=16, hidden_dims=[8], num_classes=5, dropout=0.1)
    logits = model(torch.randn(4, 16))
    assert tuple(logits.shape) == (4, 5)


def test_fair_concat_summary_marks_test_as_frozen_if_present() -> None:
    path = Path("results/internal/fair_concat/fair_concat_run_summary.json")
    if not path.exists():
        return
    import json

    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["signal_embedding_dim"] > 5
    assert summary["structured_feature_dim"] == 531
    assert summary["early_stopping_split"] == "val"
    assert summary["threshold_tuning_split"] == "val"
    assert summary["test_role"] == "frozen_final_evaluation_only"


def test_fair_concat_outputs_evaluator_compatible_schema_if_present() -> None:
    path = Path("results/internal/fair_concat/fair_concat_test_predictions.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    required = {"ecg_id", "NORM_true", "NORM_prob", "MI_true", "MI_prob", "STTC_true", "STTC_prob", "CD_true", "CD_prob", "HYP_true", "HYP_prob"}
    assert required.issubset(df.columns)
