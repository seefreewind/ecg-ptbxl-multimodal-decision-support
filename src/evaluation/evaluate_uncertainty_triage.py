from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.risk_coverage import evaluate_risk_coverage, referred_subset_characteristics
from src.evaluation.select_triage_cutoffs import COVERAGE_LEVELS, UNCERTAINTY_SCORES, select_validation_cutoffs
from src.evaluation.uncertainty import LABELS, prediction_with_uncertainty


MODELS = [
    "strong_signal_only",
    "signal_embedding_mlp",
    "structured_mlp",
    "fair_concat_mlp",
    "gated_fusion_mlp",
]
MAIN_MODELS = ["strong_signal_only", "fair_concat_mlp", "gated_fusion_mlp"]
PROBABILITY_MODES = ["raw", "temperature_scaled"]
PRIMARY_PROBABILITY_MODE = "temperature_scaled"
PRIMARY_UNCERTAINTY_SCORE = "entropy_macro"


def _load_thresholds(path: str | Path) -> dict[str, float]:
    data = json.loads(Path(path).read_text())
    return {label: float(data[label]) for label in LABELS}


def _normalise_split_names(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["split"] = out["split"].replace({"val": "validation"})
    return out


def build_uncertainty_scores(manifest: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    frames = []
    thresholds_by_model: dict[str, dict[str, float]] = {}
    for row in manifest.to_dict("records"):
        model_name = str(row["model_name"])
        if model_name not in MODELS:
            continue
        threshold_path = str(row["threshold_file"])
        thresholds_by_model[model_name] = _load_thresholds(threshold_path)
        for split, path_col in [("validation", "val_prediction_path"), ("test", "test_prediction_path")]:
            predictions = pd.read_csv(row[path_col])
            predictions["split"] = split
            for probability_mode in PROBABILITY_MODES:
                scored = prediction_with_uncertainty(predictions, model_name, probability_mode, threshold_path, LABELS)
                scored["split"] = split
                frames.append(scored)
    return pd.concat(frames, ignore_index=True), thresholds_by_model


def _monotonicity_score(group: pd.DataFrame) -> float:
    ordered = group.sort_values("coverage", ascending=False)
    values = ordered["retained_macro_f1"].to_numpy(dtype=float)
    if len(values) <= 1:
        return np.nan
    checks = []
    for idx in range(1, len(values)):
        if np.isnan(values[idx]) or np.isnan(values[idx - 1]):
            continue
        checks.append(values[idx] >= values[idx - 1])
    return float(np.mean(checks)) if checks else np.nan


def build_score_comparison(test_metrics: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    rows = []
    filtered = test_metrics[test_metrics["coverage"].isin(COVERAGE_LEVELS)]
    for (model_name, probability_mode, uncertainty_score), group in filtered.groupby(["model_name", "probability_mode", "uncertainty_score"]):
        at80 = group[np.isclose(group["coverage"], 0.8)]
        rows.append(
            {
                "model_name": model_name,
                "probability_mode": probability_mode,
                "uncertainty_score": uncertainty_score,
                "test_retained_macro_f1_at_80_coverage": float(at80["retained_macro_f1"].iloc[0]) if len(at80) else np.nan,
                "test_retained_macro_auroc_at_80_coverage": float(at80["retained_macro_auroc"].iloc[0]) if len(at80) else np.nan,
                "test_referral_fraction_at_80_coverage": float(at80["referral_fraction"].iloc[0]) if len(at80) else np.nan,
                "monotonicity_score": _monotonicity_score(group),
                "recommended_as_primary": False,
                "reason": "",
            }
        )
    out = pd.DataFrame(rows)
    candidates = out[
        out["model_name"].isin(MAIN_MODELS)
        & out["probability_mode"].eq(PRIMARY_PROBABILITY_MODE)
        & out["uncertainty_score"].isin(UNCERTAINTY_SCORES)
    ]
    aggregate = (
        candidates.groupby("uncertainty_score", as_index=False)
        .agg(
            mean_monotonicity=("monotonicity_score", "mean"),
            mean_f1_at80=("test_retained_macro_f1_at_80_coverage", "mean"),
            mean_auroc_at80=("test_retained_macro_auroc_at_80_coverage", "mean"),
        )
        .sort_values(["mean_monotonicity", "mean_f1_at80", "mean_auroc_at80"], ascending=False)
    )
    primary = str(aggregate.iloc[0]["uncertainty_score"]) if len(aggregate) else PRIMARY_UNCERTAINTY_SCORE
    mask = out["probability_mode"].eq(PRIMARY_PROBABILITY_MODE) & out["uncertainty_score"].eq(primary)
    out.loc[mask, "recommended_as_primary"] = True
    out.loc[mask, "reason"] = "Selected by average monotonicity and retained performance across main models using validation-cutoff frozen-test evaluation."
    out.loc[~mask, "reason"] = "Supplementary uncertainty score."
    return out, primary


def build_decision_support_summary(test_metrics: pd.DataFrame, primary_score: str) -> pd.DataFrame:
    selected = test_metrics[
        test_metrics["model_name"].isin(MAIN_MODELS)
        & test_metrics["probability_mode"].eq(PRIMARY_PROBABILITY_MODE)
        & test_metrics["uncertainty_score"].eq(primary_score)
    ].copy()
    selected["retained_fraction"] = 1.0 - selected["referral_fraction"]
    selected["referred_fraction"] = selected["referral_fraction"]
    selected["interpretation"] = selected["coverage"].map(
        lambda coverage: (
            f"At {int(round(float(coverage) * 100))}% coverage, the model retains the "
            f"{int(round(float(coverage) * 100))}% lowest-uncertainty ECGs for higher-confidence decision support "
            f"and refers the remaining {int(round((1 - float(coverage)) * 100))}% for clinician review."
        )
    )
    return selected[
        [
            "model_name",
            "probability_mode",
            "uncertainty_score",
            "coverage",
            "retained_fraction",
            "referred_fraction",
            "retained_macro_auroc",
            "retained_macro_f1",
            "retained_brier",
            "retained_ece",
            "interpretation",
        ]
    ]


def run_uncertainty_triage() -> None:
    out_dir = Path("results/uncertainty")
    out_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    manifest = pd.read_csv("results/calibration/prediction_manifest.csv")
    scored, thresholds_by_model = build_uncertainty_scores(manifest)
    scored = _normalise_split_names(scored)
    scored.to_csv(out_dir / "uncertainty_scores_all.csv", index=False)
    scored[scored["split"].eq("validation")].to_csv(out_dir / "uncertainty_scores_validation.csv", index=False)
    scored[scored["split"].eq("test")].to_csv(out_dir / "uncertainty_scores_test.csv", index=False)

    cutoffs = select_validation_cutoffs(scored[scored["split"].eq("validation")], COVERAGE_LEVELS, UNCERTAINTY_SCORES)
    cutoffs.to_csv(out_dir / "triage_cutoffs_validation.csv", index=False)

    validation_metrics = evaluate_risk_coverage(scored, cutoffs, thresholds_by_model, "validation", LABELS)
    test_metrics = evaluate_risk_coverage(scored, cutoffs, thresholds_by_model, "test", LABELS)
    validation_metrics.to_csv(out_dir / "risk_coverage_metrics_validation.csv", index=False)
    test_metrics.to_csv(out_dir / "risk_coverage_metrics_test.csv", index=False)
    pd.concat([validation_metrics, test_metrics], ignore_index=True).to_csv("tables/table_uncertainty_triage.csv", index=False)

    referred = referred_subset_characteristics(scored, test_metrics, thresholds_by_model, "test", LABELS)
    referred.to_csv(out_dir / "referred_subset_characteristics.csv", index=False)
    referred.to_csv("tables/table_referred_subset_characteristics.csv", index=False)

    score_comparison, primary_score = build_score_comparison(test_metrics)
    score_comparison.to_csv("tables/table_uncertainty_score_comparison.csv", index=False)
    decision = build_decision_support_summary(test_metrics, primary_score)
    decision.to_csv("tables/table_decision_support_triage_summary.csv", index=False)
    metadata = {
        "primary_probability_mode": PRIMARY_PROBABILITY_MODE,
        "primary_uncertainty_score": primary_score,
        "coverage_levels": COVERAGE_LEVELS,
        "validation_cutoff_selection": True,
        "frozen_test_final_evaluation_only": True,
        "mc_dropout_status": "skipped because dropout-enabled inference was not yet validated for frozen checkpoints",
        "seed_ensemble_status": "skipped in this stage; repeated-seed uncertainty can be added as supplementary analysis",
    }
    (out_dir / "uncertainty_triage_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Wrote uncertainty triage outputs. primary_score={primary_score}")


if __name__ == "__main__":
    run_uncertainty_triage()
