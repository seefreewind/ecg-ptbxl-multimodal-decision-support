from __future__ import annotations

from pathlib import Path

import pandas as pd
import torch


def test_gated_fusion_outputs_logits_and_gate() -> None:
    from src.models.gated_fusion import GatedFusionMLP

    model = GatedFusionMLP(signal_dim=8, structured_dim=12, hidden_dim=16, classifier_hidden_dim=8, num_classes=5)
    logits, gate = model(torch.randn(4, 8), torch.randn(4, 12), return_gate=True)

    assert tuple(logits.shape) == (4, 5)
    assert tuple(gate.shape) == (4, 16)
    assert float(gate.detach().min()) >= 0.0
    assert float(gate.detach().max()) <= 1.0


def test_gated_fusion_uses_fair_inputs_if_present() -> None:
    path = Path("results/internal/gated_fusion/gated_fusion_run_summary.json")
    if not path.exists():
        return
    import json

    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["signal_embedding_dim"] > 5
    assert summary["structured_feature_dim"] == 531
    assert summary["early_stopping_split"] == "val"
    assert summary["threshold_tuning_split"] == "val"
    assert summary["test_role"] == "frozen_final_evaluation_only"


def test_gated_fusion_outputs_schema_if_present() -> None:
    path = Path("results/internal/gated_fusion/gated_fusion_test_predictions.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    required = {"ecg_id", "NORM_true", "NORM_prob", "MI_true", "MI_prob", "STTC_true", "STTC_prob", "CD_true", "CD_prob", "HYP_true", "HYP_prob"}
    assert required.issubset(df.columns)
