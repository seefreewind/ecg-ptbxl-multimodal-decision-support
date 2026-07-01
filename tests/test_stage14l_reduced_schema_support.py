from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.training.train_ablation_mlp import AblationDataset
from src.training.train_fair_concat_fusion import FairFusionDataset


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]


def _write_reduced_frame(path: Path, n_struct: int = 2) -> None:
    rows = []
    for idx in range(4):
        row = {"ecg_id": idx + 1, "split": "train"}
        for emb_idx in range(8):
            row[f"signal_emb_{emb_idx:03d}"] = float(emb_idx)
        for struct_idx in range(n_struct):
            row[f"struct_feature_{struct_idx}"] = float(struct_idx)
        for label in LABELS:
            row[label] = int(idx % 2 == 0)
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)


def test_ablation_dataset_allows_explicit_reduced_structured_dim(tmp_path: Path) -> None:
    path = tmp_path / "reduced.csv"
    _write_reduced_frame(path)
    ds = AblationDataset(path, LABELS, "structured", expected_structured_dim=2)
    assert len(ds.feature_cols) == 2


def test_ablation_dataset_keeps_531_default_for_structured(tmp_path: Path) -> None:
    path = tmp_path / "reduced.csv"
    _write_reduced_frame(path)
    with pytest.raises(ValueError, match="expected 531"):
        AblationDataset(path, LABELS, "structured")


def test_fair_fusion_dataset_allows_explicit_reduced_structured_dim(tmp_path: Path) -> None:
    path = tmp_path / "reduced.csv"
    _write_reduced_frame(path)
    ds = FairFusionDataset(path, LABELS, expected_structured_dim=2)
    assert len([col for col in ds.feature_cols if col.startswith("struct_")]) == 2
