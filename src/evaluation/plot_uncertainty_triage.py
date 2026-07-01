from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


MAIN_MODELS = ["strong_signal_only", "fair_concat_mlp", "gated_fusion_mlp"]


def _primary_score() -> str:
    comparison = pd.read_csv("tables/table_uncertainty_score_comparison.csv")
    selected = comparison[comparison["recommended_as_primary"].astype(bool)]
    if len(selected):
        return str(selected.iloc[0]["uncertainty_score"])
    return "entropy_macro"


def _plot_metric(data: pd.DataFrame, metric: str, ylabel: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for model in MAIN_MODELS:
        group = data[data["model_name"].eq(model)].sort_values("coverage")
        ax.plot(group["coverage"] * 100, group[metric], marker="o", linewidth=1.8, label=model)
    ax.set_xlabel("Coverage retained (%)")
    ax.set_ylabel(ylabel)
    ax.set_xlim(48, 102)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_uncertainty_triage() -> None:
    figure_dir = Path("figures/uncertainty")
    figure_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path("results/uncertainty")
    metrics = pd.read_csv(out_dir / "risk_coverage_metrics_test.csv")
    primary = _primary_score()
    source = metrics[
        metrics["model_name"].isin(MAIN_MODELS)
        & metrics["probability_mode"].eq("temperature_scaled")
        & metrics["uncertainty_score"].eq(primary)
    ].copy()
    source.to_csv(out_dir / "risk_coverage_curve_source_data.csv", index=False)
    _plot_metric(source, "retained_macro_f1", "Retained macro F1", figure_dir / "risk_coverage_macro_f1.png")
    _plot_metric(source, "retained_macro_auroc", "Retained macro AUROC", figure_dir / "risk_coverage_macro_auroc.png")
    _plot_metric(source, "referral_fraction", "Referral fraction", figure_dir / "risk_coverage_referral_tradeoff.png")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, metric, title in zip(
        axes,
        ["retained_macro_auroc", "retained_macro_f1", "retained_ece"],
        ["Macro AUROC", "Macro F1", "ECE"],
    ):
        for model in MAIN_MODELS:
            group = source[source["model_name"].eq(model)].sort_values("coverage")
            ax.plot(group["coverage"] * 100, group[metric], marker="o", linewidth=1.5, label=model)
        ax.set_title(title)
        ax.set_xlabel("Coverage (%)")
    axes[0].set_ylabel("Metric value")
    axes[-1].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(figure_dir / "risk_coverage_main_models.png", dpi=300)
    plt.close(fig)
    print(f"Wrote uncertainty triage figures with primary_score={primary}")


if __name__ == "__main__":
    plot_uncertainty_triage()
