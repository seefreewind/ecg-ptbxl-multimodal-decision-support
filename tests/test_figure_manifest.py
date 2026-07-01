from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_figure_manifest_exists_and_ready_files_nonempty() -> None:
    manifest_path = Path("figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv")
    assert manifest_path.exists()
    manifest = pd.read_csv(manifest_path)
    ready = manifest[manifest["status"].eq("ready")]
    assert len(ready) > 0
    for source_file in ready["source_file"]:
        path = Path(source_file)
        assert path.exists()
        assert len(pd.read_csv(path)) > 0


def test_pending_entries_are_explicit() -> None:
    manifest = pd.read_csv("figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv")
    pending = manifest[manifest["status"].str.startswith("pending")]
    assert "pending_external_validation" in set(pending["status"])
    assert "pending_dca" not in set(pending["status"])
