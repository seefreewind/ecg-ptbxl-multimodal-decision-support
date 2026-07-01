from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.dca import LABELS, dca_by_label, load_temperature_scaled_predictions, macro_dca, threshold_grid


MAIN_MODELS = ["strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"]
SUPP_MODELS = ["signal_embedding_mlp"]


def _summary(macro: pd.DataFrame, threshold_range: str = "0.05_to_0.40") -> pd.DataFrame:
    if threshold_range == "0.05_to_0.40":
        data = macro[(macro["threshold"] >= 0.05) & (macro["threshold"] <= 0.40)]
    elif threshold_range == "0.10_to_0.30":
        data = macro[(macro["threshold"] >= 0.10) & (macro["threshold"] <= 0.30)]
    else:
        data = macro
    rows = []
    for model, group in data.groupby("model_name"):
        best = group.sort_values("macro_net_benefit", ascending=False).iloc[0]
        rows.append(
            {
                "model_name": model,
                "threshold_range": threshold_range,
                "mean_macro_net_benefit": float(group["macro_net_benefit"].mean()),
                "max_macro_net_benefit": float(best["macro_net_benefit"]),
                "threshold_at_max_macro_net_benefit": float(best["threshold"]),
                "mean_net_benefit_vs_treat_all": float(group["macro_net_benefit_vs_treat_all"].mean()),
                "mean_net_benefit_vs_treat_none": float(group["macro_net_benefit_vs_treat_none"].mean()),
                "interpretation": "Exploratory internal DCA; threshold-dependent decision-support utility only.",
            }
        )
    return pd.DataFrame(rows)


def _retained80_predictions(model_name: str, predictions: pd.DataFrame) -> pd.DataFrame:
    scores = pd.read_csv("results/uncertainty/uncertainty_scores_test.csv")
    cutoffs = pd.read_csv("results/uncertainty/triage_cutoffs_validation.csv")
    cutoff = float(
        cutoffs[
            cutoffs["model_name"].eq(model_name)
            & cutoffs["probability_mode"].eq("temperature_scaled")
            & cutoffs["uncertainty_score"].eq("entropy_macro")
            & np.isclose(cutoffs["coverage"], 0.8)
        ]["validation_uncertainty_cutoff"].iloc[0]
    )
    model_scores = scores[scores["model_name"].eq(model_name) & scores["probability_mode"].eq("temperature_scaled")][["ecg_id", "entropy_macro"]]
    merged = predictions.merge(model_scores, on="ecg_id", how="left")
    return merged[merged["entropy_macro"] <= cutoff].drop(columns=["entropy_macro"])


def _update_figure_source_data(by_label: pd.DataFrame, macro: pd.DataFrame, retained: pd.DataFrame) -> None:
    source = Path("figures/source_data")
    source.mkdir(parents=True, exist_ok=True)
    by_label.to_csv(source / "fig8_dca_by_label.csv", index=False)
    macro.to_csv(source / "fig8_dca_macro.csv", index=False)
    retained.to_csv(source / "fig8_dca_retained_80_coverage.csv", index=False)
    manifest_path = source / "FIGURE_SOURCE_DATA_MANIFEST.csv"
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)
    else:
        manifest = pd.DataFrame(columns=["figure", "panel", "source_file", "description", "generated_from", "script", "status", "last_updated", "notes"])
    manifest = manifest[manifest["figure"].ne("Figure 8")]
    manifest = manifest[
        ~(
            manifest["figure"].eq("DCA")
            & manifest["status"].astype(str).str.startswith("pending")
        )
    ]
    new_rows = pd.DataFrame(
        [
            {
                "figure": "Figure 8",
                "panel": "A/C",
                "source_file": "figures/source_data/fig8_dca_macro.csv",
                "description": "Macro decision curve analysis",
                "generated_from": "Stage 12 DCA",
                "script": "scripts/13_evaluate_dca.sh",
                "status": "ready",
                "last_updated": date.today().isoformat(),
                "notes": "Internal exploratory DCA; no clinical-readiness claim.",
            },
            {
                "figure": "Figure 8",
                "panel": "B",
                "source_file": "figures/source_data/fig8_dca_by_label.csv",
                "description": "Label-wise decision curve analysis",
                "generated_from": "Stage 12 DCA",
                "script": "scripts/13_evaluate_dca.sh",
                "status": "ready",
                "last_updated": date.today().isoformat(),
                "notes": "Binary label-wise DCA.",
            },
            {
                "figure": "Figure 8",
                "panel": "D",
                "source_file": "figures/source_data/fig8_dca_retained_80_coverage.csv",
                "description": "DCA on 80% high-confidence retained subset",
                "generated_from": "Stage 12 DCA + Stage 10 validation cutoffs",
                "script": "scripts/13_evaluate_dca.sh",
                "status": "ready",
                "last_updated": date.today().isoformat(),
                "notes": "Exploratory retained-subset analysis using validation-selected cutoffs.",
            },
        ]
    )
    pd.concat([manifest, new_rows], ignore_index=True).to_csv(manifest_path, index=False)


def _update_master_plan() -> None:
    path = Path("docs/FIGURE_MASTER_PLAN.md")
    text = path.read_text()
    if "## Figure 8. Decision curve analysis" in text:
        return
    addition = """

## Figure 8. Decision curve analysis

Panels:

- A. Macro net benefit across threshold probabilities
- B. Label-wise DCA
- C. Fair concat vs gated fusion DCA
- D. DCA in 80% high-confidence retained subset

Required source data:

- `figures/source_data/fig8_dca_macro.csv`
- `figures/source_data/fig8_dca_by_label.csv`
- `figures/source_data/fig8_dca_retained_80_coverage.csv`
"""
    path.write_text(text.rstrip() + addition + "\n")


def evaluate_dca() -> None:
    out_dir = Path("results/dca")
    out_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    grid = threshold_grid()
    grid.to_csv(out_dir / "dca_threshold_grid.csv", index=False)
    thresholds = np.sort(grid[grid["grid_name"].eq("0.01_to_0.50")]["threshold"].unique())
    by_label_frames = []
    retained_frames = []
    for model in MAIN_MODELS + SUPP_MODELS:
        pred = load_temperature_scaled_predictions(model, "test")
        by_label_frames.append(dca_by_label(model, pred, thresholds))
        if model in MAIN_MODELS:
            retained_pred = _retained80_predictions(model, pred)
            retained_label = dca_by_label(model, retained_pred, thresholds)
            retained_label["analysis_subset"] = "retained_80_coverage"
            retained_frames.append(retained_label)
    by_label = pd.concat(by_label_frames, ignore_index=True)
    macro = macro_dca(by_label)
    retained_by_label = pd.concat(retained_frames, ignore_index=True)
    retained_macro = macro_dca(retained_by_label)
    retained_macro["analysis_subset"] = "retained_80_coverage"
    by_label.to_csv(out_dir / "dca_results_by_label.csv", index=False)
    macro.to_csv(out_dir / "dca_results_macro.csv", index=False)
    retained_macro.to_csv(out_dir / "dca_results_retained_80_coverage.csv", index=False)
    by_label[by_label["model_name"].isin(MAIN_MODELS)].to_csv("tables/table_dca_by_label.csv", index=False)
    _summary(macro[macro["model_name"].isin(MAIN_MODELS)], "0.05_to_0.40").to_csv("tables/table_dca_summary.csv", index=False)
    retained_macro.to_csv("tables/table_dca_retained_80_coverage.csv", index=False)
    _update_figure_source_data(by_label[by_label["model_name"].isin(MAIN_MODELS)], macro[macro["model_name"].isin(MAIN_MODELS)], retained_macro)
    _update_master_plan()
    print("Wrote DCA results and Figure 8 source data.")


if __name__ == "__main__":
    evaluate_dca()
