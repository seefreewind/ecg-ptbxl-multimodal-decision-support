from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import torch


def test_signal_resnet_returns_high_dimensional_embedding() -> None:
    from src.models.signal_resnet import SignalResNet

    model = SignalResNet(in_channels=12, num_classes=5, base_channels=8, blocks_per_stage=(1, 1, 1))
    logits, embedding = model(torch.randn(2, 12, 1000), return_embedding=True)

    assert tuple(logits.shape) == (2, 5)
    assert embedding.shape[1] > 5


def test_signal_embedding_outputs_have_expected_schema_if_present() -> None:
    metadata = Path("data/processed/signal_embedding_metadata.json")
    if not metadata.exists():
        return
    data = json.loads(metadata.read_text(encoding="utf-8"))
    assert data["embedding_dim"] > 5
    for split, expected in [("train", 17418), ("val", 2183), ("test", 2198)]:
        path = Path(f"data/processed/signal_embeddings_strong_{split}.csv")
        assert path.exists()
        df = pd.read_csv(path)
        emb_cols = [col for col in df.columns if col.startswith("emb_")]
        assert len(df) == expected
        assert len(emb_cols) == data["embedding_dim"]
        assert df["ecg_id"].notna().all()
        assert not df["ecg_id"].duplicated().any()
