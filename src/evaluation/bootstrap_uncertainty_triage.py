from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.risk_coverage import subset_metrics
from src.evaluation.uncertainty import LABELS


MAIN_MODELS = ["strong_signal_only", "fair_concat_mlp", "gated_fusion_mlp"]
COVERAGES = [1.0, 0.9, 0.8, 0.7]
METRICS = ["retained_macro_auroc", "retained_macro_f1", "retained_brier", "retained_ece"]


def _primary_score() -> str:
    comparison = pd.read_csv("tables/table_uncertainty_score_comparison.csv")
    selected = comparison[comparison["recommended_as_primary"].astype(bool)]
    if len(selected):
        return str(selected.iloc[0]["uncertainty_score"])
    return "entropy_macro"


def _thresholds_by_model() -> dict[str, dict[str, float]]:
    manifest = pd.read_csv("results/calibration/prediction_manifest.csv")
    out = {}
    for row in manifest.to_dict("records"):
        if row["model_name"] in MAIN_MODELS:
            import json

            payload = json.loads(Path(row["threshold_file"]).read_text())
            out[str(row["model_name"])] = {label: float(payload[label]) for label in LABELS}
    return out


def bootstrap_uncertainty_triage(n_bootstrap: int = 1000, seed: int = 2026) -> pd.DataFrame:
    out_dir = Path("results/uncertainty")
    scores = pd.read_csv(out_dir / "uncertainty_scores_test.csv")
    cutoffs = pd.read_csv(out_dir / "triage_cutoffs_validation.csv")
    primary_score = _primary_score()
    thresholds = _thresholds_by_model()
    rng = np.random.default_rng(seed)
    rows = []
    for model_name in MAIN_MODELS:
        group = scores[
            scores["model_name"].eq(model_name)
            & scores["probability_mode"].eq("temperature_scaled")
        ].reset_index(drop=True)
        indices = np.arange(len(group))
        for coverage in COVERAGES:
            cutoff_row = cutoffs[
                cutoffs["model_name"].eq(model_name)
                & cutoffs["probability_mode"].eq("temperature_scaled")
                & cutoffs["uncertainty_score"].eq(primary_score)
                & np.isclose(cutoffs["coverage"], coverage)
            ].iloc[0]
            cutoff = float(cutoff_row["validation_uncertainty_cutoff"])
            retained = group[group[primary_score].to_numpy(dtype=float) <= cutoff]
            estimate = subset_metrics(retained, thresholds[model_name], LABELS)
            boot = {metric: [] for metric in METRICS}
            for _ in range(n_bootstrap):
                sample_idx = rng.choice(indices, size=len(indices), replace=True)
                sampled = group.iloc[sample_idx].reset_index(drop=True)
                sampled_retained = sampled[sampled[primary_score].to_numpy(dtype=float) <= cutoff]
                metrics = subset_metrics(sampled_retained, thresholds[model_name], LABELS)
                boot["retained_macro_auroc"].append(metrics["macro_auroc"])
                boot["retained_macro_f1"].append(metrics["macro_f1"])
                boot["retained_brier"].append(metrics["brier"])
                boot["retained_ece"].append(metrics["ece"])
            for metric in METRICS:
                values = np.asarray(boot[metric], dtype=float)
                lo, hi = np.nanpercentile(values, [2.5, 97.5])
                estimate_key = metric.replace("retained_", "")
                if estimate_key == "macro_auroc":
                    est = estimate["macro_auroc"]
                elif estimate_key == "macro_f1":
                    est = estimate["macro_f1"]
                elif estimate_key == "brier":
                    est = estimate["brier"]
                else:
                    est = estimate["ece"]
                rows.append(
                    {
                        "model_name": model_name,
                        "probability_mode": "temperature_scaled",
                        "uncertainty_score": primary_score,
                        "split": "test",
                        "coverage": coverage,
                        "metric": metric,
                        "estimate": est,
                        "ci_lower": float(lo),
                        "ci_upper": float(hi),
                        "n_bootstrap": n_bootstrap,
                        "seed": seed,
                    }
                )
    result = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    result.to_csv(out_dir / "uncertainty_triage_bootstrap_ci.csv", index=False)
    result.to_csv("tables/table_uncertainty_triage_bootstrap_ci.csv", index=False)
    return result


def main() -> None:
    result = bootstrap_uncertainty_triage()
    print(f"Wrote uncertainty triage bootstrap CI table with {len(result)} rows.")


if __name__ == "__main__":
    main()
