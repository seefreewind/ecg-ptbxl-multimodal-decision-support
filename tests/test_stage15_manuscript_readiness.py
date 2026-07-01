from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_stage15_claim_support_enforces_external_multimodal_boundary() -> None:
    path = Path("tables/table_manuscript_claim_support.csv")
    assert path.exists()
    claims = pd.read_csv(path)
    required = {
        "claim_id",
        "manuscript_claim",
        "evidence_pointer",
        "scope",
        "allowed_location",
        "risk_level",
        "required_wording_constraint",
        "forbidden_overclaim",
        "final_status",
    }
    assert required.issubset(claims.columns)
    assert len(claims) >= 18
    assert set(claims["scope"]).issubset({"internal", "signal-only-external", "reproducibility-finding", "engineering-audit-only", "forbidden"})
    assert set(claims["allowed_location"]).issubset({"main", "supplement", "audit-only", "forbidden"})
    external_multimodal = claims[claims["manuscript_claim"].str.contains("external multimodal", case=False, na=False)]
    assert not external_multimodal.empty
    assert not external_multimodal["allowed_location"].eq("main").any()


def test_stage15_external_signal_diagnostics_and_calibration_exist() -> None:
    diag = Path("tables/table_stage15_external_signal_per_class_diagnostics.csv")
    cal = Path("tables/table_stage15_external_signal_calibration.csv")
    rel = Path("tables/table_stage15_external_signal_reliability.csv")
    assert diag.exists()
    assert cal.exists()
    assert rel.exists()

    diagnostics = pd.read_csv(diag)
    assert {"dataset", "label", "prevalence", "auroc", "average_precision", "f1", "support", "threshold_source", "interpretation_note"}.issubset(diagnostics.columns)
    chapman = diagnostics[diagnostics["dataset"].eq("chapman")]
    assert {"MI", "CD", "HYP"}.issubset(set(chapman["label"]))

    calibration = pd.read_csv(cal)
    assert {"dataset", "calibration_scope", "macro_brier", "micro_brier", "macro_ece", "macro_mce", "temperature_source", "missing_artifact_note"}.issubset(calibration.columns)
    assert calibration["temperature_source"].str.contains("internal validation", case=False, na=False).all()


def test_stage15_docs_and_audit_are_ready_for_drafting() -> None:
    for path in [
        "docs/MANUSCRIPT_RESULT_BOUNDARIES.md",
        "docs/MANUSCRIPT_TITLE_ABSTRACT_FRAMING.md",
        "tables/table_figure_table_source_map.csv",
        "MANUSCRIPT_READY_AUDIT.md",
    ]:
        assert Path(path).exists(), path

    boundaries = Path("docs/MANUSCRIPT_RESULT_BOUNDARIES.md").read_text(encoding="utf-8")
    required_sentence = (
        "internal multimodal experiments remain reproducible because they use released PTB-XL+ feature values under frozen splits; "
        "the reproducibility limitation concerns de novo reconstruction of the same structured feature schema on external WFDB datasets, "
        "not reuse of the released PTB-XL+ resource"
    )
    assert required_sentence in boundaries
    assert "Forbidden claims" in boundaries

    audit = Path("MANUSCRIPT_READY_AUDIT.md").read_text(encoding="utf-8")
    assert "Stage 15 drafting decision: GO for drafting" in audit
