from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_fair_fusion_dataset_outputs_if_present() -> None:
    train_path = Path("data/processed/fair_fusion_train.csv")
    if not train_path.exists():
        return
    expected = {"train": 17418, "val": 2183, "test": 2198}
    for split, rows in expected.items():
        df = pd.read_csv(f"data/processed/fair_fusion_{split}.csv")
        signal_cols = [col for col in df.columns if col.startswith("signal_emb_")]
        struct_cols = [col for col in df.columns if col.startswith("struct_")]
        assert len(df) == rows
        assert len(signal_cols) > 5
        assert len(struct_cols) == 531
        assert df["ecg_id"].notna().all()
        assert not df["ecg_id"].duplicated().any()
        assert int(df[signal_cols + struct_cols].isna().sum().sum()) == 0
        assert set(["NORM", "MI", "STTC", "CD", "HYP", "split"]).issubset(df.columns)


def test_fair_fusion_manifest_if_present() -> None:
    manifest = Path("data/processed/fair_fusion_feature_manifest.csv")
    if not manifest.exists():
        return
    df = pd.read_csv(manifest)
    assert df["modality"].eq("signal_embedding").sum() > 5
    assert df["modality"].eq("structured").sum() == 531
