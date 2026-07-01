from __future__ import annotations

from pathlib import Path

import pandas as pd


def _write_feature_table(path: Path, rows: int = 1201) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"ecg_id": range(1, rows + 1)})
    for idx in range(25):
        df[f"qrs_duration_{idx}"] = idx
    df.to_csv(path, index=False)


def test_label_statement_files_are_excluded(tmp_path: Path) -> None:
    from src.data.validate_ptbxl_plus import inspect_candidate

    root = tmp_path / "ptbxl_plus"
    for rel in ["labels/12sl_statements.csv", "labels/ptbxl_statements.csv"]:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"ecg_id": [1, 2], "diagnostic_statement": ["MI", "NORM"]}).to_csv(path, index=False)
        row = inspect_candidate(path, root)
        assert row["excluded"] is True
        assert row["allowed_as_structured_input"] is False
        assert row["role"] == "label_or_diagnostic_statement"
        assert "target leakage" in row["exclude_reason"]


def test_official_feature_files_are_allowed(tmp_path: Path) -> None:
    from src.data.validate_ptbxl_plus import inspect_candidate

    root = tmp_path / "ptbxl_plus"
    for rel in ["features/ecgdeli_features.csv", "features/12sl_features.csv", "features/unig_features.csv"]:
        path = root / rel
        _write_feature_table(path)
        row = inspect_candidate(path, root, metadata_ids=set(map(str, range(1, 1202))))
        assert row["role"] == "allowed_feature_table"
        assert row["allowed_as_structured_input"] is True
        assert row["excluded"] is False
        assert row["score"] >= 80


def test_mapping_and_snomed_files_are_excluded(tmp_path: Path) -> None:
    from src.data.validate_ptbxl_plus import inspect_candidate

    root = tmp_path / "ptbxl_plus"
    for rel in ["labels/snomed_description.csv", "labels/mapping/ptbxlToSNOMED.csv"]:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"source_label": ["x"], "snomed": ["y"]}).to_csv(path, index=False)
        row = inspect_candidate(path, root)
        assert row["excluded"] is True
        assert row["role"] in {"label_or_diagnostic_statement", "mapping_file"}

