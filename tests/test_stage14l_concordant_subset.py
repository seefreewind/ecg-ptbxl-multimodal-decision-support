from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_stage14l_feature_manifest_uses_only_allclose_features() -> None:
    path = Path("tables/stage14l_feature_manifest.csv")
    assert path.exists()
    manifest = pd.read_csv(path)
    assert len(manifest) > 0
    assert {
        "feature_name",
        "source_stage",
        "allclose_status",
        "missingness",
        "numeric_stability_summary",
    }.issubset(manifest.columns)
    assert manifest["allclose_status"].eq("allclose_atol_1e-6_rtol_1e-6").all()


def test_stage14l_outputs_decision_and_result_tables() -> None:
    for path in [
        "docs/STAGE14L_CONCORDANT_SUBSET_SPEC.md",
        "tables/stage14l_internal_results.csv",
        "tables/stage14l_external_results.csv",
        "tables/stage14l_per_class_diagnostics.csv",
        "docs/STAGE14L_GO_NO_GO_DECISION.md",
    ]:
        assert Path(path).exists(), path

    decision_text = Path("docs/STAGE14L_GO_NO_GO_DECISION.md").read_text(encoding="utf-8")
    assert "exact PTB-XL+ reproduction" in decision_text
    assert "full 531-column external multimodal validation" in decision_text
    assert "gated fusion superiority" in decision_text

    internal = pd.read_csv("tables/stage14l_internal_results.csv")
    assert {"model", "split", "auroc", "average_precision", "f1"}.issubset(internal.columns)
    assert {"stage14l_signal_embedding_mlp", "stage14l_structured_mlp", "stage14l_fair_concat_mlp"}.issubset(set(internal["model"]))
