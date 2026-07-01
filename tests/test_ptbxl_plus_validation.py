from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_ptbxl_plus_candidate_filtering_rejects_small_structured_audit(tmp_path: Path) -> None:
    from src.data.validate_ptbxl_plus import score_candidate

    audit = tmp_path / "structured_audit.csv"
    pd.DataFrame({"ecg_id": [1, 2], "note": ["a", "b"]}).to_csv(audit, index=False)

    row = score_candidate(audit)

    assert row["excluded"] is True
    assert "structured_audit" in row["exclude_reason"]


def test_ptbxl_plus_candidate_scoring_accepts_plausible_feature_file(tmp_path: Path) -> None:
    from src.data.validate_ptbxl_plus import score_candidate

    feature_path = tmp_path / "ptbxl_plus_ecgdeli_features.csv"
    rows = 1201
    df = pd.DataFrame({"ecg_id": range(rows)})
    for idx in range(25):
        df[f"qrs_duration_{idx}"] = idx
    df.to_csv(feature_path, index=False)

    row = score_candidate(feature_path, metadata_ids=set(map(str, range(rows))))

    assert row["excluded"] is False
    assert row["score"] >= 80
    assert row["id_column"] == "ecg_id"

