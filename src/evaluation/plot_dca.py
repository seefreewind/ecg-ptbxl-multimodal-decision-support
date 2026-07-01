from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


MAIN_MODELS = ["strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"]
LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    fig.savefig(path.with_suffix(".svg"))
    plt.close(fig)


def _main_range(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["threshold"] >= 0.05) & (df["threshold"] <= 0.40)].copy()


def plot_dca() -> None:
    out_dir = Path("figures/dca")
    main_dir = Path("figures/main")
    out_dir.mkdir(parents=True, exist_ok=True)
    main_dir.mkdir(parents=True, exist_ok=True)
    macro = pd.read_csv("results/dca/dca_results_macro.csv")
    by_label = pd.read_csv("results/dca/dca_results_by_label.csv")
    retained = pd.read_csv("results/dca/dca_results_retained_80_coverage.csv")
    macro_main = _main_range(macro[macro["model_name"].isin(MAIN_MODELS)])
    by_label_main = _main_range(by_label[by_label["model_name"].isin(MAIN_MODELS)])

    fig, ax = plt.subplots(figsize=(7, 5))
    for model in MAIN_MODELS:
        g = macro_main[macro_main["model_name"].eq(model)]
        ax.plot(g["threshold"], g["macro_net_benefit"], label=model, linewidth=1.8)
    ref = macro_main[macro_main["model_name"].eq(MAIN_MODELS[0])]
    ax.plot(ref["threshold"], ref["macro_treat_all_net_benefit"], "--", color="gray", label="treat-all")
    ax.axhline(0, linestyle=":", color="black", label="treat-none")
    ax.set_title("Internal PTB-XL decision curve analysis")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Macro net benefit")
    ax.legend(frameon=False, fontsize=8)
    _save(fig, out_dir / "dca_macro_main_models.png")

    fig, axes = plt.subplots(1, len(LABELS), figsize=(16, 4), sharey=True)
    for ax, label in zip(axes, LABELS):
        sub = by_label_main[by_label_main["label"].eq(label)]
        for model in ["strong_signal_only", "fair_concat_mlp", "gated_fusion_mlp"]:
            g = sub[sub["model_name"].eq(model)]
            ax.plot(g["threshold"], g["net_benefit"], label=model, linewidth=1.2)
        ax.axhline(0, linestyle=":", color="black")
        ax.set_title(label)
        ax.set_xlabel("Threshold")
    axes[0].set_ylabel("Net benefit")
    axes[-1].legend(frameon=False, fontsize=7)
    fig.suptitle("Label-wise internal PTB-XL DCA")
    _save(fig, out_dir / "dca_by_label_main_models.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    for model in ["fair_concat_mlp", "gated_fusion_mlp"]:
        g = macro_main[macro_main["model_name"].eq(model)]
        ax.plot(g["threshold"], g["macro_net_benefit"], label=model, linewidth=2)
    ax.axhline(0, linestyle=":", color="black", label="treat-none")
    ax.set_title("Fair concat vs gated fusion DCA")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Macro net benefit")
    ax.legend(frameon=False)
    _save(fig, out_dir / "dca_fair_concat_vs_gated.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    ranges = [("0.01-0.50", 0.01, 0.50), ("0.05-0.40", 0.05, 0.40), ("0.10-0.30", 0.10, 0.30)]
    for label, lo, hi in ranges:
        g = macro[(macro["model_name"].eq("gated_fusion_mlp")) & (macro["threshold"] >= lo) & (macro["threshold"] <= hi)]
        ax.plot(g["threshold"], g["macro_net_benefit"], label=label)
    ax.axhline(0, linestyle=":", color="black")
    ax.set_title("DCA threshold range sensitivity")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Macro net benefit")
    ax.legend(frameon=False)
    _save(fig, out_dir / "dca_threshold_range_sensitivity.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    retained_main = _main_range(retained[retained["model_name"].isin(MAIN_MODELS)])
    for model in MAIN_MODELS:
        g = retained_main[retained_main["model_name"].eq(model)]
        ax.plot(g["threshold"], g["macro_net_benefit"], label=model)
    ax.axhline(0, linestyle=":", color="black", label="treat-none")
    ax.set_title("DCA in 80% high-confidence retained subset")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Macro net benefit")
    ax.legend(frameon=False, fontsize=8)
    _save(fig, out_dir / "dca_retained_80_coverage.png")

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    panels = [
        ("Full test macro DCA", macro_main, "macro_net_benefit"),
        ("Fair concat vs gated", macro_main[macro_main["model_name"].isin(["fair_concat_mlp", "gated_fusion_mlp"])], "macro_net_benefit"),
        ("80% retained subset", retained_main, "macro_net_benefit"),
        ("Net benefit vs treat-all", macro_main, "macro_net_benefit_vs_treat_all"),
    ]
    for ax, (title, data, metric) in zip(axes.ravel(), panels):
        for model in data["model_name"].drop_duplicates():
            g = data[data["model_name"].eq(model)]
            ax.plot(g["threshold"], g[metric], label=model, linewidth=1.3)
        ax.axhline(0, linestyle=":", color="black")
        ax.set_title(title)
        ax.set_xlabel("Threshold")
        ax.set_ylabel(metric)
    axes.ravel()[-1].legend(frameon=False, fontsize=7)
    fig.suptitle("Figure 8. Exploratory internal decision curve analysis")
    _save(fig, main_dir / "fig8_dca.png")
    print("Wrote DCA figures.")


if __name__ == "__main__":
    plot_dca()
