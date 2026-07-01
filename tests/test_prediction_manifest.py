from __future__ import annotations


def test_prediction_manifest_declares_main_models(tmp_path) -> None:
    from src.evaluation.collect_model_predictions import build_prediction_manifest

    manifest = build_prediction_manifest(tmp_path / "manifest.csv")

    expected = {
        "strong_signal_only",
        "signal_embedding_mlp",
        "structured_mlp",
        "fair_concat_mlp",
        "gated_fusion_mlp",
    }
    assert expected.issubset(set(manifest["model_name"]))
    assert {
        "model_name",
        "model_family",
        "val_prediction_path",
        "test_prediction_path",
        "logit_columns_available",
        "probability_columns_available",
        "threshold_file",
        "include_in_main_calibration",
        "notes",
    }.issubset(manifest.columns)
