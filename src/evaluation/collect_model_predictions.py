from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]


@dataclass(frozen=True)
class PredictionSource:
    model_name: str
    model_family: str
    val_prediction_path: str
    test_prediction_path: str
    threshold_file: str
    include_in_main_calibration: bool
    notes: str = ""


SOURCES = [
    PredictionSource(
        "strong_signal_only",
        "signal",
        "results/internal/signal_strong/signal_strong_val_predictions_with_logits.csv",
        "results/internal/signal_strong/signal_strong_test_predictions_with_logits.csv",
        "results/internal/signal_strong/val_tuned_thresholds.json",
        True,
    ),
    PredictionSource(
        "signal_embedding_mlp",
        "signal_embedding",
        "results/internal/signal_embedding_mlp/signal_embedding_mlp_val_predictions_with_logits.csv",
        "results/internal/signal_embedding_mlp/signal_embedding_mlp_test_predictions_with_logits.csv",
        "results/internal/ablation_signal_embedding/signal_embedding_mlp_thresholds.json",
        True,
    ),
    PredictionSource(
        "structured_mlp",
        "structured",
        "results/internal/structured_mlp/structured_mlp_val_predictions_with_logits.csv",
        "results/internal/structured_mlp/structured_mlp_test_predictions_with_logits.csv",
        "results/internal/ablation_structured/structured_mlp_thresholds.json",
        True,
    ),
    PredictionSource(
        "fair_concat_mlp",
        "fair_concat",
        "results/internal/fair_concat/fair_concat_val_predictions_with_logits.csv",
        "results/internal/fair_concat/fair_concat_test_predictions_with_logits.csv",
        "results/internal/fair_concat/fair_concat_thresholds.json",
        True,
    ),
    PredictionSource(
        "gated_fusion_mlp",
        "gated_fusion",
        "results/internal/gated_fusion/gated_fusion_val_predictions_with_logits.csv",
        "results/internal/gated_fusion/gated_fusion_test_predictions_with_logits.csv",
        "results/internal/gated_fusion/gated_fusion_thresholds.json",
        True,
    ),
    PredictionSource(
        "late_probability_concat",
        "supplementary_late_probability_concat",
        "results/internal/concat_fusion_val_predictions.csv",
        "results/internal/concat_fusion_test_predictions.csv",
        "",
        False,
        "supplementary non-fair late-probability comparator; excluded from main calibration comparison",
    ),
]


def _columns_available(path: Path, suffix: str) -> bool:
    if not path.exists():
        return False
    frame = pd.read_csv(path, nrows=1)
    if suffix == "logit":
        return all(f"logit_{label}" in frame.columns for label in LABELS) or all(f"{label}_logit" in frame.columns for label in LABELS)
    if suffix == "prob":
        return all(f"prob_{label}" in frame.columns for label in LABELS) or all(f"{label}_prob" in frame.columns for label in LABELS)
    return all(f"{label}_{suffix}" in frame.columns for label in LABELS)


def build_prediction_manifest(output_path: str | Path = "results/calibration/prediction_manifest.csv") -> pd.DataFrame:
    rows = []
    for source in SOURCES:
        val_path = Path(source.val_prediction_path)
        test_path = Path(source.test_prediction_path)
        threshold_path = Path(source.threshold_file) if source.threshold_file else None
        val_exists = val_path.exists()
        test_exists = test_path.exists()
        logit_available = val_exists and test_exists and _columns_available(val_path, "logit") and _columns_available(test_path, "logit")
        prob_available = val_exists and test_exists and _columns_available(val_path, "prob") and _columns_available(test_path, "prob")
        notes = source.notes
        if not val_exists or not test_exists:
            notes = f"{notes}; missing prediction file".strip("; ")
        elif not logit_available:
            notes = f"{notes}; logits unavailable, temperature scaling will be skipped".strip("; ")
        rows.append(
            {
                "model_name": source.model_name,
                "model_family": source.model_family,
                "val_prediction_path": source.val_prediction_path,
                "test_prediction_path": source.test_prediction_path,
                "logit_columns_available": bool(logit_available),
                "probability_columns_available": bool(prob_available),
                "temperature_scaling_eligible": bool(logit_available and prob_available and source.include_in_main_calibration),
                "threshold_file": source.threshold_file,
                "threshold_file_available": bool(threshold_path.exists()) if threshold_path else False,
                "include_in_main_calibration": bool(source.include_in_main_calibration),
                "notes": notes,
            }
        )
    manifest = pd.DataFrame(rows)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(out, index=False)
    return manifest


def main() -> None:
    manifest = build_prediction_manifest()
    print(f"Wrote prediction manifest with {len(manifest)} rows to results/calibration/prediction_manifest.csv")


if __name__ == "__main__":
    main()
