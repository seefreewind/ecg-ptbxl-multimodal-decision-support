from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_figure_8_source_data_files_are_registered_and_nonempty() -> None:
    expected = {
        "figures/source_data/fig8_dca_macro.csv",
        "figures/source_data/fig8_dca_by_label.csv",
        "figures/source_data/fig8_dca_retained_80_coverage.csv",
    }
    manifest = pd.read_csv("figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv")
    figure8 = manifest[manifest["figure"].eq("Figure 8")]

    assert expected.issubset(set(figure8["source_file"]))
    assert set(figure8["status"]) == {"ready"}

    for source_file in expected:
        path = Path(source_file)
        assert path.exists()
        assert path.stat().st_size > 0
        assert not pd.read_csv(path).empty


def test_completed_dca_replaces_pending_manifest_placeholder() -> None:
    manifest = pd.read_csv("figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv")
    pending_dca = manifest[
        manifest["figure"].eq("DCA")
        & manifest["status"].astype(str).str.startswith("pending")
    ]

    assert pending_dca.empty
