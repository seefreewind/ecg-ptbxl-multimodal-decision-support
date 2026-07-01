from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_ablation_configs_use_single_modalities() -> None:
    from src.utils.io import load_yaml

    signal = load_yaml("configs/model_signal_embedding_mlp.yaml")
    structured = load_yaml("configs/model_structured_mlp.yaml")
    assert signal["model"]["modality"] == "signal_embedding"
    assert structured["model"]["modality"] == "structured"


def test_ablation_outputs_if_present() -> None:
    for path in [
        Path("tables/table_signal_embedding_mlp_results.csv"),
        Path("tables/table_structured_mlp_results.csv"),
    ]:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        assert {"model", "split", "threshold_mode", "auroc", "average_precision", "f1"}.issubset(df.columns)
        assert {"val", "test"}.issubset(set(df["split"]))


def test_stage8_ablation_comparison_if_present() -> None:
    path = Path("tables/table_stage8_ablation_comparison.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    expected = {"strong signal-only", "signal-embedding MLP", "structured MLP", "fair MLP-concat", "gated fusion MLP"}
    assert expected.issubset(set(df["model"]))
